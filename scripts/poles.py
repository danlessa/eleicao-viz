import itertools
# (esquerda, direita, outlier) scores by party number
S={13:(3,0,0),50:(3,0,0),65:(2.8,0,0),16:(2.8,0,0.5),21:(2.8,0,0.5),29:(2.8,0,0.5),80:(2.8,0,0.5),
   12:(2,0,0),40:(2,0,0),18:(2,0,0.3),43:(2,0,0.3),
   22:(0,3,0),30:(0,2.5,0.5),10:(0,2,0.3),11:(0,2,0.3),44:(0,2,0.3),
   15:(0,1,1),45:(0,1,1),55:(0,1,1),
   28:(0,0.5,3),35:(0,0,2),27:(0,0.3,2),36:(0,0,2),33:(0,0,2),25:(0,0.3,2),
   20:(0,0.5,1.5),23:(0.3,0.3,1.5),70:(0,0.3,1.5),77:(1.0,0.2,1.0)}
def score(n,pole): return S.get(n,(0,0,1))[pole]
def assign(nums):
    """nums: list of candidate party numbers (2 or 3). returns list of poles (0 esq,1 dir,2 outlier) maximizing total score"""
    best=None
    for perm in itertools.permutations(range(3),len(nums)):
        s=sum(score(n,p) for n,p in zip(nums,perm))
        if best is None or s>best[0]: best=(s,perm)
    return list(best[1])
def lean(n): s=S.get(n,(0,0,1)); return s[0]-s[1]  # higher = more left
