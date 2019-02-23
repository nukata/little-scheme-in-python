#!/usr/bin/env python
"""
A little Scheme in Python 2.7/3.7 v2.0 H31.01.13/H31.02.23 by SUZUKI Hisao
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

class SchemeString:
    "String in Scheme"
    def __init__(self, string):
        self.string = string

    def __repr__(self):
        return '"' + self.string + '"'

class Closure:
    "Lambda expression with its environment"
    def __init__(self, params, body, env):
        self.params, self.body, self.env = params, body, env

    def __repr__(self):
        return stringify(self)

def stringify(exp, quote=False):
    "Convert an expression to a string."
    if exp is True:
        return '#t'
    elif exp is False:
        return '#f'
    elif isinstance(exp, List):
        ss = []
        try:
            for element in exp:
                ss.append(stringify(element, quote))
        except ImproperListError as ex:
            ss.append('.')
            ss.append(stringify(ex.args[0], quote))
        return '(' + ' '.join(ss) + ')'
    elif isinstance(exp, Closure):
        p = stringify(exp.params, True)
        b = stringify(exp.body, True)
        e = '()' if exp.env is NIL else '#' + hex(hash(exp.env))
        return '#<' + p + ':' + b + ':' + e + '>'
    elif exp is NOCONT:
        return '#<NOCONT>'
    elif isinstance(exp, tuple) and len(exp) == 4:
        op, val, env, cont = exp
        p = stringify(op, True)
        v = stringify(val, True)
        e = '()' if env is NIL else '#' + hex(hash(env))
        k = stringify(cont, True)
        return '#<' + p + ':' + v + ':' + e + ':\n ' + k + '>'
    elif isinstance(exp, SchemeString) and not quote:
        return exp.string
    else:
        return str(exp)

_ = Cell
GLOBAL_ENV = (
    _(_(intern('display'), lambda x: print(stringify(x.car), end='')),
      _(_(intern('newline'), lambda x: print()),
        _(_(intern('read'), lambda x: read_expression('', '')),
          _(_(intern('eof-object?'), lambda x: isinstance(x.car, EOFError)),
            _(_(intern('symbol?'), lambda x: isinstance(x.car, str)),
              _(_(intern('+'), lambda x: x.car + x.cdr.car),
                _(_(intern('-'), lambda x: x.car - x.cdr.car),
                  _(_(intern('*'), lambda x: x.car * x.cdr.car),
                    _(_(intern('<'), lambda x: x.car < x.cdr.car),
                      _(_(intern('='), lambda x: x.car == x.cdr.car),
                        NIL)))))))))))
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
                    assert isinstance(v, str), v
                    exp, k = kdr.cdr.car, (DEFINE, v, env, k)
                elif kar is SETQ:       # (set! v e)
                    pair = _look_for_pair(kdr.car, env)
                    exp, k = kdr.cdr.car, (SETQ, pair, env, k)
                else:
                    exp, k = kar, (APPLY, Cell(kdr, NIL), env, k)
            elif isinstance(exp, str):
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
    result = []
    for line in source_string.split('\n'):
        ss, x = [], []
        for i, e in enumerate(line.split('"')):
            if i % 2 == 0:
                x.append(e)
            else:
                ss.append('"' + e) # Append a string literal.
                x.append('#s')
        s = ' '.join(x).split(';')[0] # Ignore ;-commment.
        s = s.replace("'", " ' ").replace(')', ' ) ').replace('(', ' ( ')
        x = s.split()
        result.extend([(ss.pop(0) if e == '#s' else e) for e in x])
        assert not ss
    return result

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
    elif token[0] == '"':
        return SchemeString(token[1:])
    else:
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return intern(token) # as a symbol

def load(file_name):
    "Load a source code from a file."
    with open(file_name) as rf:
        source_string = rf.read()
    tokens = split_string_into_tokens(source_string)
    while tokens:
        exp = read_from_tokens(tokens)
        evaluate(exp)

TOKENS = []

def read_expression(prompt1='> ', prompt2='| '):
    "Read an expression."
    while True:
        old = TOKENS[:]
        try:
            return read_from_tokens(TOKENS)
        except IndexError:      # tokens.pop(0) failed unexpectedly.
            try:
                source_string = raw_input(prompt2 if old else prompt1)
            except EOFError as ex:
                del TOKENS[:]
                return ex
            TOKENS[:] = old
            TOKENS.extend(split_string_into_tokens(source_string))

def read_eval_print_loop():
    "Repeat read-eval-print until End-of-File."
    while True:
        exp = read_expression()
        if isinstance(exp, EOFError):
            print('Goodbye')
            return
        result = evaluate(exp)
        if result is not None:
            print(stringify(result, True))

if __name__ == '__main__':
    if argv[1:2]:
        load(argv[1])
        if argv[2:3] != ['-']:
            exit(0)
    read_eval_print_loop()
