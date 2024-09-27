import sys
import matplotlib.pyplot as plt


if len( sys.argv ) < 2:    
    print( "\tusage: python3 displayProfile.py filename" )
    exit()

filename = sys.argv[1]
data = []
with open(filename, 'r') as f:            
            for line in f:
                #print(line)
                l = line.split()
                x,y,z,valPixel = map(int, l[:])
                data.append((x, y, z, valPixel))


x_abscisses = list(range(1, len(data)+1))
valPixels = [d[3] for d in data]

plt.figure()
plt.plot(x_abscisses, valPixels, linestyle='-', marker='o')


plt.xlabel('(x ,y, z)')
plt.ylabel('valeur du pixel')
plt.title('Courbe du profil de densité')


plt.show()