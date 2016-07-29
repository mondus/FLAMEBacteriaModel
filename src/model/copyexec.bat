cp -v  /cygdrive/c/Users/alcione/Dropbox/flameGPU/immunemodel/model2c.py .
cp -v  /cygdrive/c/Users/alcione/Dropbox/flameGPU/immunemodel/model.json .
cp -v  /cygdrive/c/Users/alcione/Dropbox/flameGPU/immunemodel/modelgen.py .
cp -v  /cygdrive/c/Users/alcione/Dropbox/flameGPU/immunemodel/model2dot.py .
cp -v  /cygdrive/c/Users/alcione/Dropbox/flameGPU/immunemodel/testeplot.py ../../../../bin/x64/
c:\Anaconda3\python modelgen.py model.json >XMLModelFile.xml
c:\Anaconda3\python  model2dot.py -n -i XMLModelFile.xml -o saida.dot
c:\Anaconda3\python model2c.py XMLModelFile.xml model.json >functions.c
cp -v 0.xml ../../iterations/
