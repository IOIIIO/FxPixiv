git pull
chown fxpixiv -R .
chgrp www-data -R .
sudo systemctl restart fxpixiv
sudo systemctl restart fxpixivsync