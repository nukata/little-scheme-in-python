# A Little Scheme in Python

This is a small (458 lines) interpreter of a subset of Scheme.
It runs on both Python 2.7 and Python 3.8.
It implements almost the same language as

- [little-scheme-in-crystal](https://github.com/nukata/little-scheme-in-crystal)
- [little-scheme-in-cs](https://github.com/nukata/little-scheme-in-cs)
- [little-scheme-in-dart](https://github.com/nukata/little-scheme-in-dart)
- [little-scheme-in-go](https://github.com/nukata/little-scheme-in-go)
- [little-scheme-in-java](https://github.com/nukata/little-scheme-in-java)
- [little-scheme-in-kotlin](https://github.com/nukata/little-scheme-in-kotlin)
- [little-scheme-in-lisp](https://github.com/nukata/little-scheme-in-lisp)
- [little-scheme-in-php](https://github.com/nukata/little-scheme-in-php)
- [little-scheme-in-ruby](https://github.com/nukata/little-scheme-in-ruby)
- [little-scheme-in-typescript](https://github.com/nukata/little-scheme-in-typescript)

and their meta-circular interpreter, 
[little-scheme](https://github.com/nukata/little-scheme).

As a Scheme implementation, 
it optimizes _tail calls_ and handles _first-class continuations_ properly.

The implementation has been revised along with
[little-scheme-in-go](https://github.com/nukata/little-scheme-in-go)
since v3.0.
See [`archived`](archived) folder for the previous implementation.


## How to run

Run `scm.py` to start a Scheme session.

```
$ ./scm.py
> (+ 5 6)
11
> (cons 'a (cons 'b 'c))
(a b . c)
> (list
| 1
| 2
| 3
| )
(1 2 3)
> 
```

Press EOF (e.g. Control-D) to exit the session.

```
> Goodbye
$ 
```

You can run `scm.py` with a Scheme script.
Examples are found in 
[little-scheme](https://github.com/nukata/little-scheme);
download it at `..` and you can try the following:

```
$ cat ../little-scheme/examples/fib90.scm
;; Fibonacci numbers: F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1. 
;; cf. https://oeis.org/A000045
(define fibonacci
  (lambda (n)
    (define _fib
      (lambda (i F_i F_i+1)
        (if (= i n)
            F_i
          (_fib (+ i 1) F_i+1 (+ F_i F_i+1)))))
    (_fib 0 0 1)))                      ; i=0, F(0)=0, F(1)=1

(display (fibonacci 90))
(newline)
;; => 2880067194370816120
$ ./scm.py ../little-scheme/examples/fib90.scm
2880067194370816120
$ 
```

Put a "`-`" after the script in the command line to begin a session 
after running the script.

```
$ ./scm.py ../little-scheme/examples/fib90.scm -
2880067194370816120
> (fibonacci 0)
0
> (fibonacci 1)
1
> (fibonacci 16)
987
> (fibonacci 1000)
43466557686937456435688527675040625802564660517371780402481729089536555417949051
89040387984007925516929592259308032263477520968962323987332247116164299644090653
3187938298969649928516003704476137795166849228875
> 
```


You can also run
[little-scheme](https://github.com/nukata/little-scheme) with `scm.py`.
 
```
$ ./scm.py ../little-scheme/scm.scm
(+ 5 6)
=> 11
(list
1
2
3
)
=> (1 2 3)
```

```
$ ./scm.py ../little-scheme/scm.scm < ../little-scheme/examples/fib90.scm
2880067194370816120
$ 
```


## The implemented language

| Scheme Expression                   | Internal Representation             |
|:------------------------------------|:------------------------------------|
| numbers `1`, `2.3`                  | `int` or `float` (or `long`)        |
| `#t`                                | `True`                              |
| `#f`                                | `False`                             |
| strings `"hello, world"`            | `class SchemeString`                |
| symbols `a`, `+`                    | interned `str`                      |
| `()`                                | `NIL`, a singleton of `List`        |
| pairs `(1 . 2)`, `(x y z)`          | `class Cell (List)`                 |
| closures `(lambda (x) (+ x 1))`     | `class Closure`                     |
| built-in procedures `car`, `cdr`    | `class Intrinsic`                   |

- Continuations are represented by Python tuples of the form
  (_operation_, _value_, _next continuation_)
  and will be passed by `call/cc` to its argument.

- Python's native string type `str` has `intern` function.
  It is reasonable to use it as Scheme's symbol type.


### Expression types

- _v_  [variable reference]

- (_e0_ _e1_...)  [procedure call]

- (`quote` _e_)  
  `'`_e_ [transformed into (`quote` _e_) when read]

- (`if` _e1_ _e2_ _e3_)  
  (`if` _e1_ _e2_)

- (`begin` _e_...)

- (`lambda` (_v_...) _e_...)

- (`set!` _v_ _e_)

- (`define` _v_ _e_)

For simplicity, this Scheme treats (`define` _v_ _e_) as an expression type.


### Built-in procedures

|                   |                          |                 |
|:------------------|:-------------------------|:----------------|
| (`car` _lst_)     | (`display` _x_)          | (`+` _n1_ _n2_) |
| (`cdr` _lst_)     | (`newline`)              | (`-` _n1_ _n2_) |
| (`cons` _x_ _y_)  | (`read`)                 | (`*` _n1_ _n2_) |
| (`eq?` _x_ _y_)   | (`eof-object?` _x_)      | (`<` _n1_ _n2_) |
| (`pair?` _x_)     | (`symbol?` _x_)          | (`=` _n1_ _n2_) |
| (`null?` _x_)     | (`call/cc` _fun_)        | (`number?` _x_) |
| (`not` _x_)       | (`apply` _fun_ _arg_)    | (`globals`)     |
| (`list` _x_ ...)  | (`error` _reason_ _arg_) |                 |


- `(error` _reason_ _arg_`)` raises an exception with the message
  "`Error:` _reason_`:` _arg_".
  It is based on [SRFI-23](https://srfi.schemers.org/srfi-23/srfi-23.html).

- `(globals)` returns a list of keys of the global environment.
  It is not in the standard.

See [`GLOBAL_ENV`](scm.py#L190-L221)
in `scm.py` for the implementation of the procedures
except `call/cc` and `apply`.  
`call/cc` and `apply` are implemented particularly at 
[`apply_function`](scm.py#L318-L346) in `scm.py`.

I hope this serves as a popular model of how to write a Scheme interpreter
in Python.
