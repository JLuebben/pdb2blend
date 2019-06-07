from collections import OrderedDict

class DuplicateAtomError(Exception):
    pass

class PdbObject(object):
    def __init__(self, fileName):
        self._fileName = fileName
        self._atomsByEntry = OrderedDict()
        self._residues = OrderedDict()
        self._residuesByClass = {}


    def read(self):
        with open(self._fileName, 'r') as fp:
            for line in fp.readlines():
                if not line.startswith('ATOM'):
                    continue
                # print(str(''.join([str(x)[-1] for x in range(100)])))
                # print(line)
                atomId = int(line[7:11])
                atomName = line[13:16].strip()
                residueName = line[17:20].strip()
                chain = line[21].strip()
                residue = int(line[23:26])
                element = line[76:78].strip()
                position = [float(w) for w in line[31:54].strip().split() if w]
                # print(atomId, atomName, residueName, chain, residue, element, position)
                atom = Atom(atomId, atomName, residueName, position, residue, chain, element)
                # print(atom)
                self.addAtom(atom)

    def addAtom(self, atom):
        if atom.id in self._atomsByEntry:
            raise DuplicateAtomError
        self._atomsByEntry[atom.id] = atom
        residueNumber = atom.residue
        if not residueNumber in self._residues:
            resi = Residue(residueNumber, atom.residueName)
            self._residues[residueNumber] = resi
        else:
            resi = self._residues[residueNumber]
        resi.addAtom(atom)
        if not atom.residueName in self._residuesByClass:
            self._residuesByClass[atom.residueName] = []
        self._residuesByClass[atom.residueName].append(resi)

    def center(self):
        X, Y, Z = [],[],[]
        for atom in self._atomsByEntry.values():
            x, y, z = atom.position
            X.append(x)
            Y.append(y)
            Z.append(z)
        x = sum(X)/len(X)
        y = sum(Y)/len(Y)
        z = sum(Z)/len(Z)
        offset = (x,y,z)
        for atom in self._atomsByEntry.values():
            atom.translate(offset)


    def __getitem__(self, item):
        return self._residues[item]

    def __iter__(self):
        for residue in self._residues.values():
            yield residue

    def iterBackBone(self, triples=False):
        for residue in self:
            if triples:
                yield [pos for pos in residue.iterBackBone()]
            else:
                for pos in residue.iterBackBone():
                    yield pos


class Residue(object):
    def __init__(self, number, cls):
        self._number = number
        self._class = cls
        self._atoms = OrderedDict()

    def addAtom(self, atom):
        self._atoms[atom.name] = atom

    def __iter__(self):
        for atom in self._atoms.values():
            yield atom

    @property
    def position(self):
        return self._atoms['C'].position

    def iterBackBone(self):
        yield self._atoms['N'].position
        yield self._atoms['CA'].position
        yield self._atoms['C'].position

    def iterBonds(self):
        blackList = set()
        for atom1 in self._atoms.values():
            for atom2 in self._atoms.values():
                if atom1 is atom2:
                    continue
                key = tuple(sorted([atom1.name, atom2.name]))
                if key in blackList:
                    continue
                if self._dist(atom1.position, atom2.position) < 1.7:
                    yield atom1, atom2
                    blackList.add(key)

    def _dist(self, pos1, pos2):
        return sum([(p1 - p2)**2 for p1, p2 in zip(pos1, pos2)])**.5


class Atom(object):
    def __init__(self, atomId, atomName, residueName, position, residue, chain='A', element='C', ):
        self.id = atomId
        self.name = atomName
        self.residueName = residueName
        self.position = position
        self.residue = residue
        self.chain = chain
        self.element = element

    def __str__(self):
        return 'ATOM {:3} in residue {:3} at {}'.format(self.name,
                                                        self.residueName,
                                                        str(self.position))

    def translate(self, offset):
        self.position = [x-y for x, y in zip(self.position, offset)]




if __name__ == '__main__':
    pdb = PdbObject('C:/Users/arrah/Desktop/OverLayCln5Se-PPPDE1/x.pdb')
    pdb.read()
    for atom in pdb[101]:
        print(atom)
        print(atom.position)
    # for resi in pdb:
    #     print(resi.position)
    # print()
    # for pos in pdb.iterBackBone(triples=True):
    #     print(pos)
    # pdb.center()
    # for pos in pdb.iterBackBone(triples=True):
    #     print(pos)
    for bond in pdb[101].iterBonds():
        print(bond)