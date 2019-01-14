# A Little Scheme in Python 2.7 & 3.7

This is a small interpreter of a subset of Scheme.
It runs on both Python 2.7 and Python 3.7.



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


_For now_ it does _not_ optimize tail calls _nor_ handle
first-class continuations.


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

For the sake of simplicity, this Scheme treats (`define` _v_ _e_) as
an expression type and it defines _v_ as a varible at the top level 
wherever it is evaluated.


## Built-in procedures

- (`car` _lst_)

- (`cdr` _lst_)

- (`cons` _x_ _y_)

- (`eq?` _x_ _y_)

- (`eqv?` _x_ _y_)

- (`pair?` _x_)

- (`null?` _x_)

- (`not` _x_)

- (`list` _x_ ...)

- (`display` _x_)

- (`newline`)

- (`+` _x_ _y_)

- (`-` _x_ _y_)

- (`*` _x_ _y_)

- (`<` _x_ _y_)

- (`=` _x_ _y_)

See `GLOBAL_ENV` in `scm.py` for the implementation of the procedures.
