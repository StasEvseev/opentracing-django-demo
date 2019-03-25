How to upload your own package
---------------------------

1. Create at home directory `.pypirc`


    [distutils]
    index-servers =
        mypypi

    [mypypi]
    repository=http://0.0.0.0:8080/pypi
    username=admin
    password=admin

2. Go to the directory with package you want to publish and run:

`python setup.py sdist register -r mypypi`

`python setup.py sdist register upload -r mypypi`

