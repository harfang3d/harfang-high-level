del /s /f /q build\*.*
for /f %%f in ('dir /ad /b build\') do rd /s /q build\%%f
del /s /f /q dist\*.*
for /f %%f in ('dir /ad /b dist\') do rd /s /q dist\%%f
del /s /f /q HarfangHighLevel.egg-info\*.*
for /f %%f in ('dir /ad /b HarfangHighLevel.egg-info\') do rd /s /q HarfangHighLevel.egg-info\%%f

python setup.py bdist_wheel
pip uninstall -y HarfangHighLevel
pip install .\dist\HarfangHighLevel-3.1.1-py3-none-any.whl