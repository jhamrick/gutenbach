@ECHO OFF
IF "x%1x" == "xx" (
	ECHO Usage: configure "path to MIT Kerberos for Windows SDK"
	EXIT /B 1
)
SET KRB5SDK=%~f1

copy /y config.h.w32 config.h > nul
copy /y Makefile.w32 Makefile > nul

setlocal
FOR /F "usebackq tokens=2 delims='=" %%i in (`findstr /R "^PACKAGE_VERSION=" configure`) DO SET VERSION=%%i
FOR /F "usebackq tokens=1 delims=." %%i in ('%VERSION%') DO SET MAJOR=%%i
FOR /F "usebackq tokens=2 delims=." %%i in ('%VERSION%') DO SET MINOR=%%i

echo #define PACKAGE_BUGREPORT "rra@stanford.edu" >> config.h
echo #define PACKAGE_NAME "remctl" >> config.h
echo #define PACKAGE_STRING "remctl %MAJOR%.%MINOR%" >> config.h
echo #define PACKAGE_TARNAME "remctl" >> config.h
echo #define PACKAGE_VERSION "%MAJOR%.%MINOR%" >> config.h
echo #define VERSION_MAJOR %MAJOR% >> config.h
echo #define VERSION_MAJOR_STR "%MAJOR%" >> config.h
echo #define VERSION_MINOR %MINOR% >> config.h
echo #define VERSION_MINOR_STR "%MINOR%" >> config.h
