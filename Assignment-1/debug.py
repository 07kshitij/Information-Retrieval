import collections

with open('out.txt', 'r') as file:
    l = file.readline()
    l = l[1:-2]
    # print(l.split(','))
    l = l.split()
    m = []
    for x in l:
        x = x.strip()
        if x[-1] == ',':
            x = x[:-1]
        m.append(int(x))
    print([item for item, count in collections.Counter(m).items() if count > 1])

