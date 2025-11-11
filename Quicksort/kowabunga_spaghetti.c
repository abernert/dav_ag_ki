/*
Copyright 2025 Alexander Bernert

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define V volatile
#define S static
#define U unsigned
#define W while
#define I if
#define E else
#define O0(x) do{ (void)(x); } while(0)
#define NIL ((void*)0)
#define BOOL int
#define TRUE 1
#define FALSE 0


#define AT(C,idx) ((C)->a[(idx)])
#define N(C) ((C)->n)
#define PIVOT_MAGIC(a,b,c) do{ if((a)>(b)) {int _t=(a);(a)=(b);(b)=_t;} if((b)>(c)) {int _t=(b);(b)=(c);(c)=_t;} if((a)>(b)) {int _t=(a);(a)=(b);(b)=_t;} }while(0)
#define SWAPi(a,b) do{ int *_A=&(a), *_B=&(b); if(_A!=_B){ int _T=* _A; *_A = *_B; *_B=_T; } }while(0)
#define XOR_SWAP(a,b) do{ if(&(a)!=&(b)){ (a)^=(b); (b)^=(a); (a)^=(b);} }while(0)
#define ODD(x) ((x)&1)
#define EVEN(x) (!ODD(x))
#define LIKELY(x)   (x)
#define UNLIKELY(x) (x)


typedef struct Ctx {
    int           *a;
    long           n;
    V U long       chaos;
    long           seed;
    int          (*cmp)(const int*, const int*);
} Ctx;

S int cmp_default(const int* x, const int* y) { return (*x > *y) - (*x < *y); }


S void Q1(Ctx*, long, long);
S void Q2(Ctx*, long, long);
S void Q3(Ctx*, long, long);


S void (*QQ[3])(Ctx*, long, long) = { Q1, Q2, Q3 };

S U long lcg(U long *s) { *s = (*s * 1664525u + 1013904223u); return *s; }

S void ins_sometimes(Ctx* c, long L, long R) {
    long i=L+1, j; int *A = c->a;
    for (; i<=R; ++i){
        int key = A[i];
        for (j=i-1; j>=L && ((c->cmp? c->cmp(&key, &A[j]) : (key - A[j])) < 0); --j)
            A[j+1] = A[j];
        A[j+1] = key;
    }
}


S void partition_like(Ctx* c, long L, long R, long *out_i, long *out_j) {
    int *A = c->a; long i=L, j=R; 

    long m = (L ^ R) >> 1; m += L; 
    int a = A[L], b = A[m], d = A[R];
    PIVOT_MAGIC(a,b,d);
    if (A[m] != b) {
        if (A[L] == b) SWAPi(A[L], A[m]);
        else if (A[R] == b) SWAPi(A[R], A[m]);
        else A[m] = b; 
    }

    int pivot = A[m];


L_again:
    while ((c->cmp ? c->cmp(&A[i], &pivot) : (A[i] - pivot)) < 0) ++i;
    while ((c->cmp ? c->cmp(&A[j], &pivot) : (A[j] - pivot)) > 0) --j;

    if (i <= j) {

        if (EVEN(i ^ j)) { XOR_SWAP(A[i], A[j]); }
        else             { SWAPi(A[i], A[j]); }
        ++i; --j;
        if (i <= j) goto L_again;
    }

    *out_i = i; *out_j = j;
}

S void Q1(Ctx* c, long L, long R) {
    if (L >= R) { c->chaos += (U long)(R-L+1); return; }
    if (R - L < 16) { ins_sometimes(c, L, R); return; }

    long i, j; partition_like(c, L, R, &i, &j);


    int k = (int)(lcg((U long*)&c->seed) % 3u);
    if (L < j) QQ[k](c, L, j);
    k = (int)(lcg((U long*)&c->seed) % 3u);
    if (i < R) QQ[k](c, i, R);
}

S void Q2(Ctx* c, long L, long R) {

    switch ((R<=L) ? 0 : (R-L<16 ? 1 : 2)) {
        case 0: c->chaos ^= (U long)(R|L); return;
        case 1: ins_sometimes(c, L, R); return;
        default: {
            long i, j; partition_like(c, L, R, &i, &j);
            int k = (int)((c->seed = c->seed*1103515245u + 12345u) % 3u);
            if (L < j) QQ[k](c, L, j);
            k = (int)((c->seed = c->seed*1103515245u + 12345u) % 3u);
            if (i < R) QQ[k](c, i, R);
        }
    }
}

S void Q3(Ctx* c, long L, long R) {

    long i, j;
    if (!(R>L)) { c->chaos += 1; return; }
    if ((R-L) < 16) { ins_sometimes(c, L, R); return; }

    partition_like(c, L, R, &i, &j);


    goto LEFT;
RIGHT:
    if (i < R) { long Li=i, Rr=R; R = Rr; L = Li; partition_like(c, L, R, &i, &j); goto LEFT; }
    return;
LEFT:
    if (L < j) { long Ll=L, Rj=j; QQ[(int)(c->chaos%3)](c, Ll, Rj); }
    goto RIGHT;
}


void kowabunga_spaghetti(int *a, int n) {
    Ctx ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.a = a;
    ctx.n = n;
    ctx.cmp = cmp_default;  
    ctx.seed = (long)(uintptr_t)a ^ (long)time(NULL) ^ (long)n;


    QQ[(ctx.seed >> 3) % 3](&ctx, 0, (long)n - 1);


    if (n > 1) {
        V int *vp = (V int*)a;
        *vp += 0; 
    }
}


#ifdef DEMO
int main(int argc, char** argv) {
    int *A = NULL; int n = 0, cap = 0, x;
    if (argc > 1) {
        n = argc - 1; cap = n; A = (int*)malloc(sizeof(int)*cap);
        for (int i=1;i<argc;i++) A[i-1] = atoi(argv[i]);
    } else {

        while (scanf("%d", &x) == 1) {
            if (n==cap) { cap = cap? cap*2 : 16; A = (int*)realloc(A, sizeof(int)*cap); }
            A[n++] = x;
        }
        if (!A) { int tmp[] = {42, -7, 13, 13, 0, 99, -100, 5, 1, 2, 3};
                  n = (int)(sizeof(tmp)/sizeof(tmp[0]));
                  A = (int*)malloc(sizeof(int)*n);
                  memcpy(A, tmp, sizeof(tmp));
        }
    }

    kowabunga_spaghetti(A, n);

    for (int i=0;i<n;i++) {
        if (i) putchar(' ');
        printf("%d", A[i]);
    }
    putchar('\n');
    free(A);
    return 0;
}
#endif
