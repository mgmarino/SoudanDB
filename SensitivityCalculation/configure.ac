#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.


AC_PREREQ(2.50)
AC_INIT([pyWIMP])
AC_CONFIG_SRCDIR([pyWIMP/WIMPPdfs//MGMVWimpFormFactor.hh])

echo "Run ./configure --help for a list of options"
echo

AC_CANONICAL_HOST

# defaults, these will work for linux
# but NOT in screen.  Perhaps a fix for this?
BOLD=`tput bold`
# doing host os specific things
EXTRALIBFLAGS=""
EXTRACPPFLAGS=""
SOFLAGS="-shared"
PYWIMPLIBEXTSHARED=so
case "${host_os}" in
  darwin*)
  EXTRALIBFLAGS="-bind_at_load" 
  SOFLAGS="-dynamiclib"
  PYWIMPLIBEXTSHARED=dylib
  BOLD=`tput smso`
esac
OFFBOLD=`tput rmso`

# doing host cpu (i.e. architecture) specific things

case "${host_cpu}" in
  x86_64*)
  EXTRACPPFLAGS="-fPIC"
  echo "Compiling on an x86_64 chipset...Setting -fPIC flag."
  # only on amd64 should one compile static libs with this flag
  # Other tested architectures currently compile PIC libraries
  # and so it is no problem to link a dynamic library using the PIC
  # libs
esac

DIRECTORIES="pyWIMP/WIMPPdfs"
AC_SUBST(DIRECTORIES)
AC_SUBST(EXTRALIBFLAGS)
AC_SUBST(EXTRACPPFLAGS)
AC_SUBST(SOFLAGS)
AC_SUBST(PYWIMPLIBEXTSHARED)
# end host

#Find root
echo ""
echo "${BOLD}Checking for ROOT: ${OFFBOLD} "
m4_include(root.m4)
HAVE_ROOT=""
ROOT_PATH(5.24,HAVE_ROOT="yes", HAVE_ROOT="no")
if test x"$HAVE_ROOT" = xno; then
  AC_MSG_ERROR(ROOT not found, please install)
fi
HAS_ROOFIT=`$ROOTCONF --has-roofit`
if test x"$HAS_ROOFIT" = xno; then
  AC_MSG_ERROR(ROOT not installed with RooFit, please reinstall)
fi

#end root


# checking to compile as debug?
AC_ARG_ENABLE(debug, AC_HELP_STRING([--enable-debug],[Enables compiling with debug flags.]),
  [ if test "x$enableval"="xyes"; then
     enable_debug=yes
    else
     enable_debug=no
    fi
   ] 
  ,[enable_debug=no])
if test "x$enable_debug" = "xyes" ; then
  EXTRACXXFLAGS="-g"
  echo
  echo "${BOLD}Configuring with debug flags ON. ${OFFBOLD}"
else
  EXTRACXXFLAGS="-O2"
  echo ""
  echo "${BOLD}Configuring with debug flags OFF. ${OFFBOLD}"
  echo "Debug flags enabled by passing --enable-debug to configure."
fi
AC_SUBST(EXTRACXXFLAGS)

# checking to compile shared / static libs?
AC_ARG_ENABLE(shared, AC_HELP_STRING([--disable-shared],[Disables compiling of shared object libraries.]),,[enable_shared=yes])
AC_ARG_ENABLE(static, AC_HELP_STRING([--disable-static],[Disables compiling of static object libraries.]),,[enable_static=yes])
ALLTARGETDEPS="shared static"
if test ! "x$enable_shared" = "xyes" ; then
  if test ! "x$enable_static" = "xyes" ; then
  AC_MSG_ERROR([
    You may not disable both shared (--disable-shared) and static (--disable-static) libraries.  
    Please check your arguments to configure and try again.
  ])
  fi
  ALLTARGETDEPS="static"
  echo
  echo "${BOLD}Only static libraries will be built. ${OFFBOLD}"
fi
if test ! "x$enable_static" = "xyes" ; then
  ALLTARGETDEPS="shared"
  echo
  echo "${BOLD}Only shared-object libraries will be built. ${OFFBOLD}"
fi
AC_SUBST(ALLTARGETDEPS)

AC_CONFIG_FILES([
                 buildTools/config.mk
                 Makefile])
AC_OUTPUT
echo 
echo "**********************************************************************************"
echo "**********************************************************************************"
echo
echo "You have successfully configured MGDO.  Please now compile by issuing the command:"
echo 
echo "     make"
echo 


