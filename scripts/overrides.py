# Manual pole overrides where the empirical correlation with Lula 2022 mislabels a candidate.
# {CD_MUNICIPIO: {NR_VOTAVEL: pole}}; pole 0 = ~Lula (orange; red in 2T), 1 = ~Bolsonaro (teal; blue in 2T),
# 2 = outlier (purple in 1T; in 2T it takes whichever side the other finalist leaves free).
POLE_OVERRIDES={
    66893:{13:0},              # Mauá: PT ~Lula
    70777:{20:2,22:1},         # São Caetano do Sul: PODE outlier, PL ~Bolsonaro
    65510:{40:0,20:2},         # Itapevi: PSB ~Lula, PODE outlier
    71579:{45:0,20:2,44:1},    # Taboão da Serra: PSDB ~Lula, PODE outlier, UNIÃO ~Bolsonaro
    63770:{15:2},              # Diadema: MDB outlier
}

def assign_poles(m,nrs):
    """nrs: candidate numbers sorted by r_lula22 descending (2 or 3 of them). returns list of poles, same order."""
    default=[0,2,1] if len(nrs)==3 else [0,1]
    ov=POLE_OVERRIDES.get(m,{}); fixed={nr:ov[nr] for nr in nrs if nr in ov}
    if not fixed: return default
    free=[p for p in ([0,2,1] if len(nrs)==3 else [0,1,2]) if p not in fixed.values()]
    return [fixed[nr] if nr in fixed else free.pop(0) for nr in nrs]

def sort_key_2t(m,nr,r):
    """2T: key for ordering the pair (higher -> pole A / red). overridden ~Lula/~Bolsonaro win outright."""
    p=POLE_OVERRIDES.get(m,{}).get(nr)
    return 9 if p==0 else -9 if p==1 else r
