# A Little Scheme in Python

This is a small (≈ 400 lines) interpreter of a subset of Scheme.
It runs on both Python 2.7 and Python 3.7.
As a Scheme implementation, 
it optimizes _tail calls_ and handles _first-class continuations_ properly.

The implementation has been revised along with
[little-scheme-in-go](https://github.com/nukata/little-scheme-in-go).
See [`archived`](archived) folder for the previous implementation.


## How to use

Run `scm.py` to start a Scheme session.

```
$ chmod a+x scm.py
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

```
$ cat examples/fib90.scm
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
$ ./scm.py examples/fib90.scm
2880067194370816120
$ 
```

Put a "`-`" after the script in the command line to begin a session 
after running the script.

```
$ ./scm.py examples/fib90.scm -
2880067194370816120
> (fibonacci 0)
0
> (fibonacci 1)
1
> (fibonacci 16)
987
> 
```


## Examples

There are four files under the `examples` folder.

- [`fib90.scm`](examples/fib90.scm)
  calculates Fibonacci for 90 tail-recursively.

- [`nqueens.scm`](examples/nqueens.scm)
  runs an N-Queens solver for 6.

- [`dynamic-wind-example.scm`](examples/dynamic-wind-example.scm)
  demonstrates the example of `dynamic-wind` in R5RS.

- [`yin-yang-puzzle.scm`](examples/yin-yang-puzzle.scm)
  runs the yin-yang puzzle with `call/cc`.

```
$ ./scm.py examples/nqueens.scm
((5 3 1 6 4 2) (4 1 5 2 6 3) (3 6 2 5 1 4) (2 4 6 1 3 5))
$ ./scm.py examples/dynamic-wind-example.scm 
(connect talk1 disconnect connect talk2 disconnect)
$ cat examples/yin-yang-puzzle.scm
;; The yin-yang puzzle 
;; cf. https://en.wikipedia.org/wiki/Call-with-current-continuation

((lambda (yin)
   ((lambda (yang)
      (yin yang))
    ((lambda (cc)
       (display '*)
       cc)
     (call/cc (lambda (c) c)))))
 ((lambda (cc)
    (newline)
    cc)
  (call/cc (lambda (c) c))))

;; => \n*\n**\n***\n****\n*****\n******\n...
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
```

Press the interrupt key (e.g. Control-C) to stop the yin-yang puzzle.

For a large example, try
[little-scheme](https://github.com/nukata/little-scheme),
which is a meta-circular interpreter of this Scheme.


## The implemented language

| Scheme Expression                   | Internal Representation             |
|:------------------------------------|:------------------------------------|
| numbers `1`, `2.3`                  | `int` or `float`                    |
| `#t`                                | `True`                              |
| `#f`                                | `False`                             |
| strings `"hello, world"`            | `class SchemeString`                |
| symbols `a`, `+`                    | interned `str`                      |
| `()`                                | `NIL`, a singleton of `List`        |
| pairs `(1 . 2)`, `(x y z)`          | `class Cell (List)`                 |
| closures `(lambda (x) (+ x 1))`     | `class Closure`                     |
| built-in procedures `car`, `cdr`    | `class Intrinsic`                   |

Continuations are represented by Python tuples of the form
(_operation_, _value_, _next continuation_)
and will be passed by `call/cc` to its argument.

Python's native string type `str` has `intern` function.
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

|                      |                       |                     |
|:---------------------|:----------------------|:--------------------|
| (`car` _lst_)        | (`not` _x_)           | (`eof-object?` _x_) |
| (`cdr` _lst_)        | (`list` _x_ ...)      | (`symbol?` _x_)     |
| (`cons` _x_ _y_)     | (`call/cc` _fun_)     | (`+` _x_ _y_)       |
| (`eq?` _x_ _y_)      | (`apply` _fun_ _arg_) | (`-` _x_ _y_)       |
| (`eqv?` _x_ _y_)     | (`display` _x_)       | (`*` _x_ _y_)       |
| (`pair?` _x_)        | (`newline`)           | (`<` _x_ _y_)       |
| (`null?` _x_)        | (`read`)              | (`=` _x_ _y_)       |
|                      |                       | (`globals`)         |

`(globals)` returns a list of keys of the global environment.
It is not in the standard.

See [`GLOBAL_ENV`](scm.py#L168-L194)
in `scm.py` for the implementation of the procedures
except `call/cc` and `apply`.  
`call/cc` and `apply` are implemented particularly at 
[`apply_function`](scm.py#L289-L317) in `scm.py`.

I hope this serves as a popular model of how to write a Scheme interpreter
in Python.
