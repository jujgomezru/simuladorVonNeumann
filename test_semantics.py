import pytest
from bigraph_parser import parse_bigraph
from bigraph_semantics import SemanticsProcessor, SemanticError

def test_var_decl_semantics():
    text = '''
      int x;
      float A[3][2] = 1.5;
      char c = 'z';
    '''
    ast = parse_bigraph(text)
    proc = SemanticsProcessor()
    env, _ = proc.process(ast)

    assert env.get('x') is None
    assert env.get('A', [0,0]) == 1.5
    assert env.get('c') == 'z'
