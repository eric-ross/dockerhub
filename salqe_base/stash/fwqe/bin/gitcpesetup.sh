cd $HOME
for i in 2013 2014 2015
do
  rm -f products${i}
  ln -s /mnt/fwqenfs/fwqeuser/products${i} products${i}
done
