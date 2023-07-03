# Build dependencies:
pip install -r requirements.txt --target ./build
pip install \
    --platform manylinux2014_x86_64 \
    --target=./build \
    --implementation cp \
    --python 3.9 \
    --only-binary=:all: --upgrade \
    'psycopg[binary,pool]'

# Move required application files into build:
cp *.py build/.
cp swagger.json build/.
cp -R config build/.

cd build/
zip -qr build.zip *