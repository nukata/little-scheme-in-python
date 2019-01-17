#!/usr/bin/env python
"""
 A little Scheme in Python 2.7 & 3.7  H31.1/13 - H31.1/17 by SUZUKI Hisao
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
NOCONT = ()                     # NOCONT means there is no continuation.
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
    elif exp is NOCONT:
        return '#<NOCONT>'
    elif isinstance(exp, tuple) and len(exp) == 4:
        op, val, env, cont = exp
        p = stringify(op)
        v = stringify(val)
        e = '()' if env is NIL else '#' + hex(hash(env))
        k = stringify(cont)
        return '#<' + p + ':' + v + ':' + e + ':\n ' + k + '>'
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
    elif op is DEFINE:          # x = v
        env.cdr = Cell(env.car, env.cdr)
        env.car = Cell(x, exp)
        return (None, None, k)
    elif op is SETQ:            # x = (v . e)
        x.cdr = exp
        return (None, None, k)
    elif op is APPLY:           # x = (arguments . evaluated)
        args, evaled = x.car, Cell(exp, x.cdr)
        if args is NIL:
            evaled = _reverse(evaled)
            return apply_function(evaled.car, evaled.cdr, k)
        else:
            return (args.car, env, (APPLY, Cell(args.cdr, evaled), env, k))
    else:
        raise ValueError((cont, exp))

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

def _reverse(lst, result=NIL):
    "_reverse((a b c d)) => (d c b a)"
    if lst is NIL:
        return result
    else:
        return _reverse(lst.cdr, Cell(lst.car, result))

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

def read_eval_print(source_string):
    "Read-eval-print a source string."
    result = None
    tokens = split_string_into_tokens(source_string)
    while tokens:
        exp = read_from_tokens(tokens)
        result = evaluate(exp)
    if result is not None:
        print(stringify(result))

def read_eval_print_loop():
    "Repeat read-eval-print until End-of-File."
    while True:
        try:
            source_string = raw_input('> ')
        except EOFError:
            print('Goodbye')
            return
        read_eval_print(source_string)

if __name__ == '__main__':
    if argv[1:2]:
        source_string = open(argv[1]).read()
        read_eval_print(source_string)
        if argv[2:3] != ['-']:
            exit(0)
    read_eval_print_loop()
