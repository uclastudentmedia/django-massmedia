from setuptools import setup, find_packages

setup(
    name='django-massmedia',
    version = '0.1',
    description = 'Allows for site staff can upload and edit the media files through the site, and the filesystem is maintained in the background.',
    author='Weston Nielson',
    url='https://code.launchpad.net/~wnielson/django-massmedia/devel',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools', 'setuptools_bzr'],
)
