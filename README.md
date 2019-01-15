# A Little Scheme in Python

This is a small (300 lines) interpreter of a subset of Scheme.
It runs on both Python 2.7 and Python 3.7.
As a Scheme implementation, 
it optimizes _tail calls_ and handles _first-class continuations_ properly.


## How to use

Run `scm.py` to start a Scheme session.

```
$ chmod a+x scm.py
$ ./scm.py
> (+ 5 6)
11
> (cons 'a (cons 'b 'c))
(a b . c)
> 
```

Sorry, but each whole expression must be input in _a_ line
on the session.  You cannot divide it into lines.

Press EOF (e.g. Control-D) to exit the session.

```
> Goodbye
$ 
```

You can run `scm.py` with a Scheme script.

```
$ cat examples/fib15.scm
(define fib
  (lambda (n)
    (if (< n 2)
        1
      (+ (fib (- n 1))
         (fib (- n 2))))))

(display (fib 15))
(newline)
;; => 987
$ ./scm.py examples/fib15.scm
987
$ 
```

Put a "`-`" after the script to begin a session after running it.

```
$ ./scm.py examples/fib15.scm -
987
> (fib 0)
1
> (fib 1)
1
> (fib 2)
2
> 
```


## Examples

There are three files under the `examples` folder.

- [`fib15.scm`](examples/fib15.scm)
  calculates Fibonacci for 15.

- [`nqueens.scm`](examples/nqueens.scm)
  runs an N-Queens solver for 6.

- [`yin-yang-puzzle.scm`](examples/yin-yang-puzzle.scm)
  runs the yin-yang puzzle with `call/cc`.

```
$ ./scm.py examples/nqueens.scm
((5 3 1 6 4 2) (4 1 5 2 6 3) (3 6 2 5 1 4) (2 4 6 1 3 5))
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


## The implemented language

This Scheme does not have strings.

| Scheme Expression                   | Internal Representation               |
|:------------------------------------|:--------------------------------------|
| numbers `1`, `2.3`                  | `int` or `float`                      |
| `#t`                                | `True`                                |
| `#f`                                | `False`                               |
| symbols `a`, `+`                    | interned `str`                        |
| `()`                                | `NIL`, a singleton of `List()`        |
| pairs `(1 . 2)`, `(x y z)`          | `class Cell (List)`                   |
| closures `(lambda (x) (+ x 1))`     | `class Closure`                       |

Continuations are represented by Python tuples of the form
(_operation_, _value_, _environment_, _next continuation_)
and will be passed by `call/cc` to its argument.


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

- (`car` _lst_)

- (`cdr` _lst_)

- (`cons` _x_ _y_)

- (`eq?` _x_ _y_)

- (`eqv?` _x_ _y_)

- (`pair?` _x_)

- (`null?` _x_)

- (`not` _x_)

- (`list` _x_ ...)

- (`call/cc` _fun_)

- (`apply` _fun_ _arg_)

- (`display` _x_)

- (`newline`)

- (`+` _x_ _y_)

- (`-` _x_ _y_)

- (`*` _x_ _y_)

- (`<` _x_ _y_)

- (`=` _x_ _y_)

See [`GLOBAL_ENV`](scm.py#L91-L112)
in `scm.py` for the implementation of the procedures
except `call/cc` and `apply`.  
`call/cc` and `apply` are implemented at 
[`apply_function`](scm.py#L183-L202) in `scm.py`.

I hope `scm.py` serves as a popular model of
how to write a Scheme interpreter in Python.
