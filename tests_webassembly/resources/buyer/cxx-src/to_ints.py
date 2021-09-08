import sys

sys.stdout.write('[')
for c in sys.stdin.buffer.read():
    sys.stdout.write(str(c))
    sys.stdout.write(',')
sys.stdout.write(']')
    
