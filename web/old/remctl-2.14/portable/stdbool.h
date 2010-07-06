/*
 * Portability wrapper around <stdbool.h>.
 *
 * Provides the bool and _Bool types and the true and false constants,
 * following the C99 specification, on hosts that don't have stdbool.h.  This
 * logic is based heavily on the example in the Autoconf manual.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * This work is hereby placed in the public domain by its author.
 */

#ifndef PORTABLE_STDBOOL_H
#define PORTABLE_STDBOOL_H 1

#if HAVE_STDBOOL_H
# include <stdbool.h>
#else
# if HAVE__BOOL
#  define bool _Bool
# else
#  ifdef __cplusplus
typedef bool _Bool;
#  elif _WIN32
#   include <windef.h>
#   define bool BOOL
#  else
typedef unsigned char _Bool;
#   define bool _Bool
#  endif
# endif
# define false 0
# define true  1
# define __bool_true_false_are_defined 1
#endif

/*
 * If we define bool and don't tell Perl, it will try to define its own and
 * fail.  Only of interest for programs that also include Perl headers.
 */
#ifndef HAS_BOOL
# define HAS_BOOL 1
#endif

#endif /* !PORTABLE_STDBOOL_H */
