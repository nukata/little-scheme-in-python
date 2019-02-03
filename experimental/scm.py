#!/usr/bin/env python
"""
A little Scheme in Python 2.7/3.7 exp.v. H31.01.13/H31.02.03 by SUZUKI Hisao
"""
from __future__ import print_function
from types import FunctionType
from sys import argv, exit
try:
    from sys import intern      # for Python 3.7
    raw_input = input           # for Python 3.7
except ImportError:
    pass                        # for Python 2.7

class List:
    "Empty list"
    def __repr__(self):
        return stringify(self)

    def __iter__(self):
        return iter(())

NIL = List()
QUOTE = intern('quote')         # Use an interned string as a symbol.
IF = intern('if')
BEGIN = intern('begin')
LAMBDA = intern('lambda')
DEFINE = intern('define')
SETQ = intern('set!')
APPLY = intern('apply')
CALLCC = intern('call/cc')

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

class ImproperListError (Exception):
    pass

class Closure:
    "Lambda expression with its environment"
    def __init__(self, params, body, env):
        self.params, self.body, self.env = params, body, env

    def __repr__(self):
        return stringify(self)

def stringify(exp):
    "Convert an expression to a string."
    if exp is True:
        return '#t'
    elif exp is False:
        return '#f'
    elif isinstance(exp, List):
        ss = []
        try:
            for element in exp:
                ss.append(stringify(element))
        except ImproperListError as ex:
            ss.append('.')
            ss.append(stringify(ex.args[0]))
        return '(' + ' '.join(ss) + ')'
    elif isinstance(exp, Closure):
        p = stringify(exp.params)
        b = stringify(exp.body)
        e = '()' if exp.env is NIL else '#' + hex(hash(exp.env))
        return '#<' + p + ':' + b + ':' + e + '>'
    else:
        return str(exp)

_ = Cell
GLOBAL_ENV = (
    _(_(intern('display'), lambda x: print(stringify(x.car), end='')),
      _(_(intern('newline'), lambda x: print()),
        _(_(intern('load'), lambda x: read_eval_print(open(x.car).read())),
          _(_(intern('symbol->string'), lambda x: x.car),
            _(_(intern('+'), lambda x: x.car + x.cdr.car),
              _(_(intern('-'), lambda x: x.car - x.cdr.car),
                _(_(intern('*'), lambda x: x.car * x.cdr.car),
                  _(_(intern('<'), lambda x: x.car < x.cdr.car),
                    _(_(intern('='), lambda x: x.car == x.cdr.car),
                      NIL))))))))))
GLOBAL_ENV = (
    _(_(intern('car'), lambda x: x.car.car),
      _(_(intern('cdr'), lambda x: x.car.cdr),
        _(_(intern('cons'), lambda x: Cell(x.car, x.cdr.car)),
          _(_(intern('eq?'), lambda x: x.car is x.cdr.car),
            _(_(intern('eqv?'), lambda x: x.car == x.cdr.car),
              _(_(intern('pair?'), lambda x: isinstance(x.car, Cell)),
                _(_(intern('null?'), lambda x: x.car is NIL),
                  _(_(intern('not'), lambda x: x.car is False),
                    _(_(intern('list'), lambda x: x),
                      _(_(CALLCC, CALLCC),
                        _(_(APPLY, APPLY),
                          GLOBAL_ENV))))))))))))


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
        elif kar is BEGIN:      # (begin e...)
            return _eval_sequentially(kdr, env, k)
        elif kar is LAMBDA:     # (lambda (v...) e...)
            return k(Closure(kdr.car, kdr.cdr, env))
        elif kar is DEFINE:     # (define v e)
            v, e = kdr.car, kdr.cdr.car
            assert isinstance(v, str), v # as a symbol
            return evaluate(e, env, lambda x: k(_define(v, x, env)))
        elif kar is SETQ:       # (set! v e)
            v, e = kdr.car, kdr.cdr.car
            pair = _look_for_pair(v, env)
            return evaluate(e, env, lambda x: k(_setq(pair, x)))
        else:
            return evaluate(kar, env, lambda fun:
                                _evlis(kdr, env, lambda arg:
                                           apply_function(fun, arg, k)))
    elif isinstance(exp, str):  # as a symbol
        pair = _look_for_pair(exp, env)
        return k(pair.cdr)
    else:                       # as a number, #t, #f etc.
        return k(exp)

def apply_function(fun, arg, k):
    "Apply a function to arguments with a continuation."
    if fun is CALLCC:
        return apply_function(arg.car, Cell(lambda x: k(x.car), NIL), k)
    elif fun is APPLY:
        return apply_function(arg.car, arg.cdr.car, k)
    elif isinstance(fun, FunctionType):
        return k(fun(arg))
    elif isinstance(fun, Closure):
        env = _pair_keys_and_data_on_alist(fun.params, arg, fun.env)
        return _eval_sequentially(fun.body, env, k)
    else:
        raise ValueError((fun, arg))

def _eval_sequentially(explist, env, k, result=None):
    if explist is NIL:
        return k(result)
    else:
        return evaluate(explist.car, env,
                        lambda x: _eval_sequentially(explist.cdr, env, k, x))

def _evlis(arg, env, k):
    if arg is NIL:
        return k(NIL)
    else:
        kar, kdr = arg.car, arg.cdr
        return evaluate(kar, env, lambda head:
                            _evlis(kdr, env, lambda tail:
                                       k(Cell(head, tail))))

def _define(v, e, env):
    env.cdr = Cell(env.car, env.cdr)
    env.car = Cell(v, e)

def _setq(pair, e):
    pair.cdr = e

def _look_for_pair(key, alist):
    "_look_for_pair(b, ((a . 1) (b . 2) (c . 3))) => (b . 2)"
    for pair in alist:
        if pair.car is key:
            return pair
    raise NameError(key)

def _pair_keys_and_data_on_alist(keys, data, alist):
    "_pair_keys_and_data_on_alist((a b), (1 2), x) => ((a . 1) (b . 2) . x)"
    if keys is NIL:
        return alist
    else:
        return Cell(Cell(keys.car, data.car),
                    _pair_keys_and_data_on_alist(keys.cdr, data.cdr, alist))


def split_string_into_tokens(source_string):
    "split_string_into_tokens('(a 1)') => ['(', 'a', '1', ')']"
    s = '\n'.join([x.split(';')[0] for x in source_string.split('\n')])
    s = s.replace("'", " ' ")
    s = s.replace(')', ' ) ')
    s = s.replace('(', ' ( ')
    return s.split()

def read_from_tokens(tokens):
    """Read an expression from a list of token strings.
    The list will be left with the rest of token strings, if any.
    """
    token = tokens.pop(0)
    if token == '(':
        y = z = Cell(NIL, NIL)
        while tokens[0] != ')':
            if tokens[0] == '.':
                tokens.pop(0)
                y.cdr = read_from_tokens(tokens)
                if tokens[0] != ')':
                    raise SyntaxError(') is expected')
                break
            e = read_from_tokens(tokens)
            y.cdr = Cell(e, NIL)
            y = y.cdr
        tokens.pop(0)
        return z.cdr
    elif token == ')':
        raise SyntaxError('unexpected )')
    elif token == "'":
        e = read_from_tokens(tokens)
        return Cell(QUOTE, Cell(e, NIL)) # 'e => (quote e)
    elif token == '#f':
        return False
    elif token == '#t':
        return True
    else:
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return intern(token) # as a symbol

class IncompleteExpressionError (Exception):
    pass

def read_eval_print(source_string):
    "Read-eval-print a source string."
    result = None
    tokens = split_string_into_tokens(source_string)
    while tokens:
        try:
            exp = read_from_tokens(tokens)
        except IndexError:      # tokens.pop(0) failed unexpectedly.
            raise IncompleteExpressionError(source_string)
        result = evaluate(exp)
    if result is not None:
        print(stringify(result))

def read_eval_print_loop():
    "Repeat read-eval-print until End-of-File."
    initial = True
    while True:
        try:
            if initial:
                source_string = raw_input('> ')
            else:               # Add a continuation line.
                source_string += '\n' + raw_input('| ')
                initial = True
        except EOFError:
            print('Goodbye')
            return
        try:
            read_eval_print(source_string)
        except IncompleteExpressionError as ex:
            if ex.args[0] is source_string:
                initial = False
            else:
                raise

if __name__ == '__main__':
    if argv[1:2]:
        source_string = open(argv[1]).read()
        read_eval_print(source_string)
        if argv[2:3] != ['-']:
            exit(0)
    read_eval_print_loop()
