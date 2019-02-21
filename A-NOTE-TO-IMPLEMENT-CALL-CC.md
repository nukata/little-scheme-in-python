# A Note to Implement Call/CC

<a name="1"></a>
## 1. Problem: CPS alone does not suffice

It is well known that _first-class continuations_ and the function
`call/cc` (Call with Current Continuation) as found in Scheme can be
implemented trivially by writing the interpreter in _CPS_
(Continuation Passing Style).
 You can find such an example written in Common Lisp at
[_"Common Lisp de tsukuru micro Scheme (3)"_](http://www.geocities.jp/m_hiroi/clisp/clispb14.html)
and another example written in Java at
[_"Java de Kēzoku no tukaeru Scheme o jissō-suru"_](http://qiita.com/saka1029/items/9d8b3658d001d28942d6)
(or [SchemeWithContinuation](https://github.com/saka1029/SchemeWithContinuation)).

[experimental/scm.py](experimental/scm.py) is such an example I wrote in Python experimentally.


In this example, the evaluator function `evaluate` begins as follows:

```Python
def evaluate(exp, env=GLOBAL_ENV, k=lambda x: x):
    "Evaluate an expression with an environment and a continuation."
    if isinstance(exp, Cell):
        kar, kdr = exp.car, exp.cdr
        if kar is QUOTE:        # (quote e)
            return k(kdr.car)
        elif kar is IF:         # (if e1 e2 e3) or (if e1 e2)
            e1, e2, rest = kdr.car, kdr.cdr.car, kdr.cdr.cdr
            e3 = None if rest is NIL else rest.car
            return evaluate(e1, env, 
                            lambda x: evaluate(e2 if x else e3, env, k))
```

where `NIL` is defined as follows:

```Python
class List:
    "Empty list"
    def __repr__(self):
        return stringify(self)

    def __iter__(self):
        return iter(())

NIL = List()
```

and `Cell` is defined as follows:

```Python
class Cell (List):
    "Cons cell"
    def __init__(self, car, cdr):
        self.car, self.cdr = car, cdr

    def __iter__(self):
        "Yield car, cadr, caddr and so on."
        j = self
        while isinstance(j, Cell):
            yield j.car
            j = j.cdr
        if j is not NIL:
            raise ImproperListError(j)
```


The function `evaluate` has an additional parameter `k` which represents the continuation.

In the case of `(quote e)`, the evaluation result `e` (= `kdr.car`) will be passed to `k`.

In the case of `(if e1 e2 e3)`, the expression `e1` will be passed to `evaluate` with
the current environment `env` and a new continuation `lambda x: evaluate(e2 if x else e3, env, k))`,
which will receive the evaluation result of `e1` as the lambda parameter `x`.

The application function `apply_function` also has the `k` parameter.

```Python
def apply_function(fun, arg, k):
    "Apply a function to arguments with a continuation."
    if fun is CALLCC:
        return apply_function(arg.car, Cell(Continuation(k), NIL), k)
    elif fun is APPLY:
        return apply_function(arg.car, arg.cdr.car, k)
    elif isinstance(fun, Continuation):
        return fun.cont(arg.car)
    elif isinstance(fun, FunctionType):
        return k(fun(arg))
    elif isinstance(fun, Closure):
        env = _pair_keys_and_data_on_alist(fun.params, arg, fun.env)
        return _eval_sequentially(fun.body, env, k)
    else:
        raise ValueError((fun, arg))
```

where `CALLCC` represents `call/cc` and `APPLY` represents `apply`.

`Continuation` is defined as follows:

```Python
class Continuation:
    "Continuation as an expression value"
    def __init__(self, cont):
        self.cont = cont

    def __str__(self):
        return '#<' + hex(hash(self.cont)) + '>'
```

`FunctionType` is imported from `types` as follows:

```Python
from types import FunctionType
```

and `_eval_sequentially` is defined as follows:

```Python
def _eval_sequentially(explist, env, k, result=None):
    if explist is NIL:
        return k(result)
    else:
        return evaluate(explist.car, env,
                        lambda x: _eval_sequentially(explist.cdr, env, k, x))
```

Such an implementation of first-class continuations is simple and elegant.
However, it has a defect depending on the underlying language. 
CPS alone does not suffice.

That is, _it will have a huge call depth if the underlying language
(Python in this case) does not optimize tail calls._

Consider a nested invocation _k(f(a))_.   
First, the interpreter evaluates the inner application _f(a)_ and will get the result _x_.
Then it returns to the place from which it called the function _f_ and evaluates _k(x)_ there.
In short, it calls and returns and calls and returns: _x = f(a); k(x)_.  
The call depth will be one.

Now, consider _f(a, k)_ which is in Continuation Passing Style.  
The interpreter calls the function _f_ with _a_ and the continuation _k_.
Without returning from _f_, it will tail-call _k(x)_.
In short, it calls and calls and returns and returns.
The call depth will be two. 

Therefore, [the yin-yang puzzle](examples/yin-yang-puzzle.scm) will fail very soon:

```
$ ./experimental/scm.py examples/yin-yang-puzzle.scm

*
**
***
****
*****
***Traceback (most recent call last):
  File "./experimental/scm.py", line 278, in <module>
    read_eval_print(source_string)
[snip]
  File "./experimental/scm.py", line 168, in <lambda>
    k(Cell(head, tail))))
RuntimeError: maximum recursion depth exceeded while calling a Python object
$ 
```


<a name="2"></a>
## 2. Solution: non-recursive nested loops


In Continuation Passing Style, an evaluation result will be passed to its _continuation_.
A new evaluation and a new continuation will be produced within the continuation.
When the continuation runs out, the evaluator terminates.

To implement the above with a limited call depth, you can use nested loops as follows:

```Python
def evaluate(exp, env=GLOBAL_ENV, k=NOCONT):
    "Evaluate an expression with an environment and a continuation."
    while True:
        while env is not None: # None as env means expr has been evaluated.
            if isinstance(exp, Cell):
                kar, kdr = exp.car, exp.cdr
                if kar is QUOTE:        # (quote e)
                    exp, env = kdr.car, None
                elif kar is IF:         # (if e1 e2 e3) or (if e1 e2)
                    exp, k = kdr.car, (IF, kdr.cdr, env, k)
                elif kar is BEGIN:      # (begin e...)
                    exp, k = kdr.car, (BEGIN, kdr.cdr, env, k)
                elif kar is LAMBDA:     # (lambda (v...) e...)
                    exp, env = Closure(kdr.car, kdr.cdr, env), None
                elif kar is DEFINE:     # (define v e)
                    v = kdr.car
                    assert isinstance(v, str), v # as a symbol
                    exp, k = kdr.cdr.car, (DEFINE, v, env, k)
                elif kar is SETQ:       # (set! v e)
                    pair = _look_for_pair(kdr.car, env)
                    exp, k = kdr.cdr.car, (SETQ, pair, env, k)
                else:
                    exp, k = kar, (APPLY, Cell(kdr, NIL), env, k)
            elif isinstance(exp, str):  # as a symbol
                pair = _look_for_pair(exp, env)
                exp, env = pair.cdr, None
            else:                       # as a number, #t, #f etc.
                env = None
        if k is NOCONT:
            return exp
        else:
            exp, env, k = apply_cont(k, exp)
```

where a continuation is represented by a quadruple:
_(operation, value, environment, next continuation)_.

The function `apply_cont` begins as follows:

```Python
def apply_cont(cont, exp):
    """Apply a continuation to an expression.
    It returns (expression, environment, continuation).
    """
    op, x, env, k = cont
    if op is IF:                # x = (e2 e3)
        if exp is False:
            if x.cdr is NIL:
                return (None, env, k)
            else:
                return (x.cdr.car, env, k) # (e3, env, k)
        else:
            return (x.car, env, k) # (e2, env, k)
    elif op is BEGIN:           # x = (e...)
        if x is NIL:
            return (exp, None, k)
        else:
            return (x.car, env, (BEGIN, x.cdr, env, k))
```

Now the application function `apply_function` is defined as follows:

```Python
def apply_function(fun, arg, k):
    """Apply a function to arguments with a continuation.
    It returns (expression, environment, continuation).
    """
    while True:
        if fun is CALLCC:
            fun, arg = arg.car, Cell(k, NIL)
        elif fun is APPLY:
            fun, arg = arg.car, arg.cdr.car
        else:
            break
    if isinstance(fun, FunctionType):
        return (fun(arg), None, k)
    elif isinstance(fun, Closure):
        env = _pair_keys_and_data_on_alist(fun.params, arg, fun.env)
        return (Cell(BEGIN, fun.body), env, k)
    elif isinstance(fun, tuple): # as a continuation
        return (arg.car, None, fun)
    else:
        raise ValueError((fun, arg))
```

Note that all these functions are _not recursive_.  
_(Thus you can translate them even into FORTRAN 77 word for word if you
manage to write garbage collection in it!)_

Now you can run the yin-yang puzzle successfully:

```
$ ./scm.py examples/yin-yang-puzzle.scm

*
**
***
****
*****
******
*******
********
*********
**********
***********
************
*************
**************
***************
****************
*****************
******************
*******************
[snip]
```


