#!/usr/bin/env python
"""
 A little Scheme in Python 2.7/3.7  H31.1/13 - H31.1/14 by SUZUKI Hisao
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

class Cell (List):
    "Cons cell"
    def __init__(self, car, cdr):
        self.car, self.cdr = car, cdr

    def __iter__(self):
        "Yields car, cadr, caddr and so on."
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
        _(_(intern('+'), lambda x: x.car + x.cdr.car),
          _(_(intern('-'), lambda x: x.car - x.cdr.car),
            _(_(intern('*'), lambda x: x.car * x.cdr.car),
              _(_(intern('<'), lambda x: x.car < x.cdr.car),
                _(_(intern('='), lambda x: x.car == x.cdr.car),
                  NIL))))))))
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
                      GLOBAL_ENV))))))))))


def evaluate(exp, env):
    "eval in Scheme"
    if isinstance(exp, Cell):
        kar, kdr = exp.car, exp.cdr
        if kar is QUOTE:        # (quote e)
            return kdr.car
        elif kar is IF:         # (if e1 e2 e3) or (if e1 e2)
            if evaluate(kdr.car, env) is False:
                if kdr.cdr.cdr is NIL:
                    return None
                else:
                    return evaluate(kdr.cdr.cdr.car, env) # eval e3
            else:
                return evaluate(kdr.cdr.car, env) # eval e2
        elif kar is BEGIN:      # (begin e...)
            return _eval_sequentially(kdr, env)
        elif kar is LAMBDA:     # (lambda (v...) e...)
            return Closure(kdr.car, kdr.cdr, env)
        elif kar is DEFINE:     # (define v e)
            v = kdr.car
            assert isinstance(v, str), v # as a symbol
            e = evaluate(kdr.cdr.car, env)
            GLOBAL_ENV.cdr = Cell(GLOBAL_ENV.car, GLOBAL_ENV.cdr)
            GLOBAL_ENV.car = Cell(v, e)
        elif kar is SETQ:       # (set! v e)
            pair = _look_for_pair(kdr.car, env)
            pair.cdr = evaluate(kdr.cdr.car, env)
        else:
            return apply_function(evaluate(kar, env), _map_eval(kdr, env))
    elif isinstance(exp, str):  # as a symbol
        pair = _look_for_pair(exp, env)
        return pair.cdr
    else:                       # as a number, #t, #f etc.
        return exp

def _look_for_pair(key, alist):
    "_look_for_pair(b, ((a . 1) (b . 2) (c . 3))) => (b . 2)"
    for pair in alist:
        if pair.car is key:
            return pair
    else:
        raise NameError(key)

def _pair_keys_and_data_on_alist(keys, data, alist):
    "_pair_keys_and_data_on_alist((a b), (1 2), x) => ((a . 1) (b . 2) . x)"
    if keys is NIL:
        return alist
    else:
        return Cell(Cell(keys.car, data.car),
                    _pair_keys_and_data_on_alist(keys.cdr, data.cdr, alist))

def _eval_sequentially(explist, env):
    "_eval_sequentially(((+ 1 2) (+ 3 4)), GLOBAL_ENV) => 7"
    result = None
    for exp in explist:
        result = evaluate(exp, env)
    return result

def _map_eval(args, env):
    "_map_eval(((+ 1 2) 4), GLOBAL_ENV) => (3 4)"
    if args is NIL:
        return NIL
    else:
        return Cell(evaluate(args.car, env), _map_eval(args.cdr, env))

def apply_function(fun, arg):
    "apply in Scheme"
    if isinstance(fun, FunctionType):
        return fun(arg)
    elif isinstance(fun, Closure):
        env = _pair_keys_and_data_on_alist(fun.params, arg, fun.env)
        return _eval_sequentially(fun.body, env)
    else:
        raise ValueError(fun)


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
    if not tokens:
        raise SyntaxError('unexpected EOF')
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
        result = evaluate(exp, GLOBAL_ENV)
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
