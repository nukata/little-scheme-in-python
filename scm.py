#!/usr/bin/env python
"""
A little Scheme in Python 2.7/3.7 v3.0 H31.01.13/H31.03.24 by SUZUKI Hisao
"""
from __future__ import print_function
from sys import argv, exit
try:
    from sys import intern      # for Python 3.7
    raw_input = input           # for Python 3.7
except ImportError:
    pass                        # for Python 2.7

class List:
    "Empty list"
    __slots__ = ()

    def __iter__(self):
        return iter(())

    def __len__(self):
        n = 0
        for e in self:
            n += 1
        return n

NIL = List()
QUOTE = intern('quote')         # Use an interned string as a symbol.
IF = intern('if')
BEGIN = intern('begin')
LAMBDA = intern('lambda')
DEFINE = intern('define')
SETQ = intern('set!')
APPLY = intern('apply')
CALLCC = intern('call/cc')

NOCONT = ()                   # NOCONT means there is no continuation.
# Continuation operators
THEN = intern('then')
APPLY_FUN = intern('aplly-fun')
EVAL_ARG = intern('eval-arg')
PUSH_ARGS = intern('push-args')
RESTORE_ENV = intern('restore-env')

class Cell (List):
    "Cons cell"
    __slots__ = ('car', 'cdr')

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


class Environment:
    "Linked list of bindings mapping symbols to values"
    __slots__ = ('sym', 'val', 'next')

    def __init__(self, sym, val, next):
        "(env.sym is None) means the env is the frame top. "
        self.sym, self.val, self.next = sym, val, next

    def __iter__(self):
        "Yield each binding in the linked list."
        env = self
        while env is not None:
            yield env
            env = env.next

    def look_for(self, symbol):
        "Search the bindings for a symbol."
        for env in self:
            if env.sym is symbol:
                return env
        raise NameError(symbol)

    def prepend_defs(self, symbols, data):
        "Build an environment prepending the bindings of symbols and data."
        if symbols is NIL:
            if data is not NIL:
                raise TypeError('surplus arg: ' + stringify(data))
            return self
        else:
            if data is NIL:
                raise TypeError('surplus param: ' + stringify(symbols))
            return Environment(symbols.car, data.car,
                               self.prepend_defs(symbols.cdr, data.cdr))

class Closure:
    "Lambda expression with its environment"
    __slots__ = ('params', 'body', 'env')

    def __init__(self, params, body, env):
        self.params, self.body, self.env = params, body, env

class Intrinsic:
    "Built-in function"
    __slots__ = ('name', 'arity', 'fun')

    def __init__(self, name, arity, fun):
        self.name, self.arity, self.fun = name, arity, fun

    def __repr__(self):
        return '#<%s:%d>' % (self.name, self.arity)

def stringify(exp, quote=True):
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
    elif isinstance(exp, Environment):
        ss = []
        for env in exp:
            if env is GLOBAL_ENV:
                ss.append('GlobalEnv')
                break
            elif env.sym is None: # marker of the frame top
                ss.append('|')
            else:
                ss.append(env.sym)
        return '#<' + ' '.join(ss) + '>'
    elif isinstance(exp, Closure):
        p, b, e = [stringify(x) for x in (exp.params, exp.body, exp.env)]
        return '#<' + p + ':' + b + ':' + e + '>'
    elif isinstance(exp, tuple) and len(exp) == 3:
        p, v, k = [stringify(x) for x in exp]
        return '#<' + p + ':' + v + ':\n ' + k + '>'
    elif isinstance(exp, SchemeString) and not quote:
        return exp.string
    else:
        return str(exp)

def _globals(x):
    "Return a list of keys of the global environment."
    j, env = NIL, GLOBAL_ENV.next # Take next to skip the marker.
    for e in env:
        j = Cell(e.sym, j)
    return j

_ = lambda n, a, f, next: Environment(intern(n), Intrinsic(n, a, f), next)
GLOBAL_ENV = (
    _('display', 1, lambda x: print(stringify(x.car, False), end=''),
      _('newline', 0, lambda x: print(),
        _('read', 0, lambda x: read_expression('', ''),
          _('eof-object?', 1, lambda x: isinstance(x.car, EOFError),
            _('symbol?', 1, lambda x: isinstance(x.car, str),
              _('+', 2, lambda x: x.car + x.cdr.car,
                _('-', 2, lambda x: x.car - x.cdr.car,
                  _('*', 2, lambda x: x.car * x.cdr.car,
                    _('<', 2, lambda x: x.car < x.cdr.car,
                      _('=', 2, lambda x: x.car == x.cdr.car,
                        _('globals', 0, _globals,
                          None))))))))))))
GLOBAL_ENV = Environment(
    None, None,                 # marker of the frame top
    _('car', 1, lambda x: x.car.car,
      _('cdr', 1, lambda x: x.car.cdr,
        _('cons', 2, lambda x: Cell(x.car, x.cdr.car),
          _('eq?', 2, lambda x: x.car is x.cdr.car,
            _('eqv?', 2, lambda x: x.car == x.cdr.car,
              _('pair?', 1, lambda x: isinstance(x.car, Cell),
                _('null?', 1, lambda x: x.car is NIL,
                  _('not', 1, lambda x: x.car is False,
                    _('list', -1, lambda x: x,
                      Environment(CALLCC, CALLCC,
                                  Environment(APPLY, APPLY,
                                              GLOBAL_ENV))))))))))))


def evaluate(exp, env=GLOBAL_ENV):
    "Evaluate an expression in an environment."
    k = NOCONT
    try:
        while True:
            while True:
                if isinstance(exp, Cell):
                    kar, kdr = exp.car, exp.cdr
                    if kar is QUOTE: # (quote e)
                        exp = kdr.car
                        break
                    elif kar is IF: # (if e1 e2 e3) or (if e1 e2)
                        exp, k = kdr.car, (THEN, kdr.cdr, k)
                    elif kar is BEGIN: # (begin e...)
                        exp = kdr.car
                        if kdr.cdr is not NIL:
                            k = (BEGIN, kdr.cdr, k)
                    elif kar is LAMBDA: # (lambda (v...) e...)
                        exp = Closure(kdr.car, kdr.cdr, env)
                        break
                    elif kar is DEFINE: # (define v e)
                        v = kdr.car
                        assert isinstance(v, str), v
                        exp, k = kdr.cdr.car, (DEFINE, v, k)
                    elif kar is SETQ: # (set! v e)
                        exp, k = kdr.cdr.car, (SETQ, env.look_for(kdr.car), k)
                    else:
                        exp, k = kar, (APPLY, kdr, k)
                elif isinstance(exp, str):
                    exp = env.look_for(exp).val
                    break
                else:           # as a number, #t, #f etc.
                    break
            while True:
                if k is NOCONT:
                    return exp
                op, x, k = k
                if op is THEN:  # x = (e2 e3)
                    if exp is False:
                        if x.cdr is NIL:
                            exp = None
                        else:
                            exp = x.cdr.car # e3
                            break
                    else:
                        exp = x.car # e2
                        break
                elif op is BEGIN: # x = (e...)
                    if x.cdr is not NIL: # unless tail call...
                        k = (BEGIN, x.cdr, k)
                    exp = x.car
                    break
                elif op is DEFINE: # x = v
                    assert env.sym is None # Check for the marker.
                    env.next = Environment(x, exp, env.next)
                    exp = None
                elif op is SETQ: # x = Environment(v, e, next)
                    x.val = exp
                    exp = None
                elif op is APPLY: # x = args; exp = fun
                    if x is NIL:
                        exp, k, env = apply_function(exp, NIL, k, env)
                    else:
                        k = (APPLY_FUN, exp, k)
                        while x.cdr is not NIL:
                            k = (EVAL_ARG, x.car, k)
                            x = x.cdr
                        exp = x.car
                        k = (PUSH_ARGS, NIL, k)
                        break
                elif op is PUSH_ARGS: # x = evaluated args
                    args = Cell(exp, x)
                    op, exp, k = k
                    if op is EVAL_ARG: # exp = the next arg
                        k = (PUSH_ARGS, args, k)
                        break
                    elif op is APPLY_FUN: # exp = evaluated fun
                        exp, k, env = apply_function(exp, args, k, env)
                    else:
                        raise RuntimeError('unexpected op: %s: %s' %
                                           (stringify(op), stringify(exp)))
                elif op is RESTORE_ENV: # x = env
                    env = x
                else:
                    raise RuntimeError('bad op: %s: %s' %
                                       (stringify(op), stringify(x)))
    except Exception as ex:
        msg = type(ex).__name__ + ': ' + str(ex)
        if k is not NOCONT:
            msg += '\n ' + stringify(k)
        raise Exception(msg)

def apply_function(fun, arg, k, env):
    """Apply a function to arguments with a continuation.
    It returns (result, continuation, environment).
    """
    while True:
        if fun is CALLCC:
            k = _push_RESTORE_ENV(k, env)
            fun, arg = arg.car, Cell(k, NIL)
        elif fun is APPLY:
            fun, arg = arg.car, arg.cdr.car
        else:
            break
    if isinstance(fun, Intrinsic):
        if fun.arity >= 0:
            if len(arg) != fun.arity:
                raise TypeError('arity not matched: ' + str(fun) + ' and '
                                + stringify(arg))
        return fun.fun(arg), k, env
    elif isinstance(fun, Closure):
        k = _push_RESTORE_ENV(k, env)
        k = (BEGIN, fun.body, k)
        env = Environment(None, None, # marker of the frame top
                          fun.env.prepend_defs(fun.params, arg))
        return None, k, env
    elif isinstance(fun, tuple): # as a continuation
        return arg.car, fun, env
    else:
        raise TypeError('not a function: ' + stringify(fun) + ' with ' 
                        + stringify(arg))

def _push_RESTORE_ENV(k, env):
    if k is NOCONT or k[0] is not RESTORE_ENV: # unless tail call...
        k = (RESTORE_ENV, env, k)
    return k


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
        except IndexError:      # tokens have run out unexpectedly.
            try:
                source_string = raw_input(prompt2 if old else prompt1)
            except EOFError as ex:
                return ex
            TOKENS[:] = old
            TOKENS.extend(split_string_into_tokens(source_string))
        except SyntaxError:
            del TOKENS[:]       # Discard the erroneous tokens.
            raise

def read_eval_print_loop():
    "Repeat read-eval-print until End-of-File."
    while True:
        try:
            exp = read_expression()
            if isinstance(exp, EOFError):
                print('Goodbye')
                return
            result = evaluate(exp)
            if result is not None:
                print(stringify(result, True))
        except Exception as ex:
            print(ex)

if __name__ == '__main__':
    if argv[1:2]:
        load(argv[1])
        if argv[2:3] != ['-']:
            exit(0)
    read_eval_print_loop()
