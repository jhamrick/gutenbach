/*
 * Dummy symbol to prevent an empty library.
 *
 * On platforms that already have all of the functions that libportable would
 * supply, Automake builds an empty library and then calls ar with nonsensical
 * arguments.  Ensure that libportable always contains at least one symbol.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * This work is hereby placed in the public domain by its author.
 */

/* Prototype to avoid gcc warnings. */
int portable_dummy(void);

int
portable_dummy(void)
{
    return 42;
}
