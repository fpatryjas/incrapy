"""Sampling strategies for drawing a hand-codeable subset from the post corpus.

Each sampler takes the full DataFrame and a target size N, and returns a
DataFrame of at most N rows plus the bookkeeping columns needed downstream
(``tenure_days``, ``user_seq``, ``stratum``).

All four share the same preparation step (:func:`prepare`), which derives
tenure from ``datetime - date`` and drops posts too short to code. The
``n_post`` column is thread position, not lifetime post index, and ``n_posts``
is a scrape-time profile snapshot -- neither is used for tenure here.
"""

import warnings

import numpy as np
import pandas as pd

MIN_CHARS = 15


def prepare(df, min_chars=MIN_CHARS):
    """Derive tenure/sequence columns and drop uncodeable posts.

    Returns a copy with ``dt``, ``joined``, ``tenure_days``, ``user_seq``
    (0-based rank of the post within the user's own timeline) and
    ``user_frac`` (that rank rescaled to 0..1).
    """
    out = df.copy()
    out["dt"] = pd.to_datetime(out["datetime"], utc=True, errors="coerce")
    out["joined"] = pd.to_datetime(
        out["date"], format="%b %d, %Y", utc=True, errors="coerce"
    )

    msg = out["message"].fillna("").str.strip()
    out = out[(msg.str.len() >= min_chars) & out["dt"].notna() & out["joined"].notna()]

    out["tenure_days"] = (out["dt"] - out["joined"]).dt.days
    out = out[out["tenure_days"] >= 0]

    out = out.sort_values(["user_id", "dt"])
    out["user_seq"] = out.groupby("user_id").cumcount()
    out["user_frac"] = out["user_seq"] / (
        out.groupby("user_id")["user_seq"].transform("max").clip(lower=1)
    )
    return out


def _allocate(n_per_group, total):
    """Split ``total`` across groups as evenly as the group sizes allow.

    Groups smaller than their even share keep everything they have; the
    shortfall is redistributed across groups that still have slack, so the
    result sums to ``total`` whenever the pool is large enough.
    """
    quota = pd.Series(0, index=n_per_group.index, dtype=int)
    remaining = total
    active = n_per_group.index.tolist()

    while active and remaining > 0:
        share = max(remaining // len(active), 1)
        progressed = False
        for g in list(active):
            if remaining <= 0:
                break
            room = n_per_group[g] - quota[g]
            take = min(share, room, remaining)
            if take > 0:
                quota[g] += take
                remaining -= take
                progressed = True
            if quota[g] >= n_per_group[g]:
                active.remove(g)
        if not progressed:
            break
    return quota


def sample_proportional(df, n=1000, seed=0, min_chars=MIN_CHARS):
    """Strategy 1 -- simple random sample, proportional to user volume.

    The baseline. Mirrors the corpus as it actually is, so heavy posters
    dominate: Izayacel (22k posts) contributes ~4x what andinocel (3.5k) does.
    Use it as the comparison point that shows what the other three buy you --
    not for the tenure question, since it gives no control over when in a
    user's life the posts land.
    """
    pool = prepare(df, min_chars)
    take = min(n, len(pool))
    out = pool.sample(n=take, random_state=seed)
    out["stratum"] = "proportional"
    return out.sort_values(["user_id", "dt"])


def sample_balanced_users(df, n=1000, seed=0, min_chars=MIN_CHARS):
    """Strategy 2 -- equal posts per user (goal a).

    Every user contributes the same count, so a finding cannot be an artifact
    of one prolific poster's idiolect. With 10 users and N=1000 that is 100
    posts each. Users with fewer eligible posts than their quota give
    everything they have and the remainder is redistributed.
    """
    pool = prepare(df, min_chars)
    counts = pool.groupby("user_id").size()
    quota = _allocate(counts, min(n, len(pool)))

    rng = np.random.default_rng(seed)
    parts = [
        g.sample(n=quota[uid], random_state=rng.integers(1 << 31))
        for uid, g in pool.groupby("user_id")
        if quota[uid] > 0
    ]
    out = pd.concat(parts)
    out["stratum"] = "balanced_user"
    return out.sort_values(["user_id", "dt"])


def sample_tenure_bands(df, n=1000, seed=0, min_chars=MIN_CHARS,
                        bands=(0, 180, 545, 1095, 2190, 100_000)):
    """Strategy 3 -- balanced across user x tenure band (goals b + c).

    The workhorse for the radicalization question. Bands default to 0-6mo,
    6-18mo, 18-36mo, 36-72mo, 72mo+ of tenure, and the sample is spread evenly
    across every user-band cell that has posts. Because each user appears in
    every band, tenure becomes a *within-user* contrast: you compare AsiaCel
    early against AsiaCel late, rather than early-users against late-users.
    That kills the survivorship confound (violent users staying longer), since
    the same people appear at both ends.

    It does not fix calendar-time confounding -- all 10 users joined within a
    10-month window in 2017-18, so tenure and year move together across the
    whole frame. Keep ``dt`` in the model as a separate term and treat any
    tenure effect as tenure-or-period.
    """
    pool = prepare(df, min_chars)
    labels = [f"{bands[i]}-{bands[i + 1]}d" for i in range(len(bands) - 1)]
    pool["band"] = pd.cut(
        pool["tenure_days"], bins=list(bands), labels=labels, right=False
    )
    pool = pool[pool["band"].notna()]

    cells = pool.groupby(["user_id", "band"], observed=True).size()
    quota = _allocate(cells, min(n, len(pool)))

    rng = np.random.default_rng(seed)
    parts = [
        g.sample(n=quota[key], random_state=rng.integers(1 << 31))
        for key, g in pool.groupby(["user_id", "band"], observed=True)
        if quota[key] > 0
    ]
    out = pd.concat(parts)
    out["stratum"] = out["band"].astype(str)
    return out.sort_values(["user_id", "dt"])


def sample_onboarding_weighted(df, n=1000, seed=0, min_chars=MIN_CHARS,
                               first_k=50, early_share=0.4):
    """Strategy 4 -- dense on the first posts, thinner later (goal b emphasis).

    Spends ``early_share`` of the budget on each user's first ``first_k``
    posts, where attitudes are forming and posts are scarce, and spreads the
    rest evenly over the remainder of their timeline by quantile. Use when the
    question is "what did they sound like when they arrived, and did it
    change" and you want real resolution on the arrival rather than one
    thin band.

    Your data supports this: every user's first scraped post falls within
    30 days of their join date, so the onboarding phase is genuinely present
    and not truncated by the scrape.
    """
    pool = prepare(df, min_chars)
    n = min(n, len(pool))
    n_early = int(round(n * early_share))
    rng = np.random.default_rng(seed)

    early_pool = pool[pool["user_seq"] < first_k]
    late_pool = pool[pool["user_seq"] >= first_k]

    # early_share is a request, not a guarantee: the early pool is capped at
    # roughly first_k * n_users. Past that the shortfall silently rolls into
    # `later` and the realised share drops below the one asked for, so say so.
    if n_early > len(early_pool):
        warnings.warn(
            f"early_share={early_share} of n={n} requests {n_early} onboarding "
            f"posts but only {len(early_pool)} exist with user_seq < {first_k}; "
            f"realised early_share will be ~{len(early_pool) / n:.2f}. "
            f"Raise first_k or lower n to hit the requested share.",
            UserWarning,
            stacklevel=2,
        )

    early_quota = _allocate(early_pool.groupby("user_id").size(), n_early)
    early = [
        g.sample(n=early_quota[uid], random_state=rng.integers(1 << 31))
        for uid, g in early_pool.groupby("user_id")
        if early_quota[uid] > 0
    ]
    early = pd.concat(early) if early else pool.iloc[:0]
    early = early.assign(stratum="onboarding")

    # Whatever the early phase could not absorb rolls into the late budget.
    late_quota = _allocate(late_pool.groupby("user_id").size(), n - len(early))
    late = []
    for uid, g in late_pool.groupby("user_id"):
        k = late_quota[uid]
        if k <= 0:
            continue
        # Even coverage by quantile of the user's remaining timeline, so late
        # posts are spread across the years rather than clumped.
        edges = np.linspace(0, len(g), k + 1).astype(int)
        picks = [
            g.iloc[lo:hi].sample(n=1, random_state=rng.integers(1 << 31))
            for lo, hi in zip(edges[:-1], edges[1:]) if hi > lo
        ]
        if picks:
            late.append(pd.concat(picks))
    late = pd.concat(late) if late else pool.iloc[:0]
    late = late.assign(stratum="later")

    out = pd.concat([early, late])
    return out.sort_values(["user_id", "dt"])
