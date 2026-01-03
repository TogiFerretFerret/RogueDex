import argparse
parser=argparse.ArgumentParser()
parser.add_argument("exect",type=str)
parser.add_argument("src",type=str)
args=parser.parse_args()
import os
if (args.exect=="compile"):
    import pickle
    with open(args.src,"r") as f:
        code=f.read()
    import battledex_engine.roguescript.lexer as lexer
    import battledex_engine.roguescript.parser as parser
    import battledex_engine.roguescript.compiler as compiler
    lex=lexer.Lexer(code)
    tokens=lex.get_all_tokens()
    parse=parser.Parser(tokens)
    program=parse.parse()
    if program is None:
        print("COMPILE ERROR")
    comp=compiler.Compiler()
    bytecode=comp.compile(program)
    v=".".join(os.path.basename(args.src).split('.')[:-1])
    with open(f"{v}.rgb","wb") as f:
        pickle.dump(bytecode,f)
elif args.exect=="run":
    import pickle
    with open(args.src,"rb") as f:
        bt=pickle.load(f)
    import battledex_engine.roguescript.vm as vmprovider
    vm = vmprovider.VirtualMachine()
    r,v=vm.execute(bt)
    exit(v)
