from setuptools import setup, find_packages

setup(name='dj_portfolio',
      version='0.1',
      description='Simple portfolio tracker',
      url='',
      author='Ben Miller',
      author_email='bsmiller25@gmail.com',
      license='',
      packages=find_packages(),
      install_requires=[
          'requests',
          'django',
          'yfinance',
          'bs4',
          'lxml',
      ],
      include_package_data=True,
      zip_safe=False)
