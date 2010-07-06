/*
 * gss-tokens test suite.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>

#include <tests/tap/basic.h>
#include <tests/tap/kerberos.h>
#include <util/util.h>

extern char send_buffer[2048];
extern char recv_buffer[2048];
extern size_t send_length;
extern size_t recv_length;
extern int send_flags;
extern int recv_flags;


int
main(void)
{
    char *principal;
    gss_buffer_desc name_buf, server_tok, client_tok, *token_ptr;
    gss_name_t server_name, client_name;
    gss_ctx_id_t server_ctx, client_ctx;
    OM_uint32 c_stat, c_min_stat, s_stat, s_min_stat, ret_flags;
    gss_OID doid;
    int status, flags;

    /* Unless we have Kerberos available, we can't really do anything. */
    principal = kerberos_setup();
    if (principal == NULL)
        skip_all("Kerberos tests not configured");
    plan(26);

    /*
     * We have to set up a context first in order to do this test, which is
     * rather annoying.
     */
    name_buf.value = principal;
    name_buf.length = strlen(principal) + 1;
    s_stat = gss_import_name(&s_min_stat, &name_buf, GSS_C_NT_USER_NAME,
                             &server_name);
    if (s_stat != GSS_S_COMPLETE)
        bail("cannot import name");
    server_ctx = GSS_C_NO_CONTEXT;
    client_ctx = GSS_C_NO_CONTEXT;
    token_ptr = GSS_C_NO_BUFFER;
    do {
        c_stat = gss_init_sec_context(&c_min_stat, GSS_C_NO_CREDENTIAL,
                                      &client_ctx, server_name,
                                      (const gss_OID) GSS_KRB5_MECHANISM,
                                      GSS_C_MUTUAL_FLAG | GSS_C_REPLAY_FLAG,
                                      0, NULL, token_ptr, NULL, &client_tok,
                                      &ret_flags, NULL);
        if (token_ptr != GSS_C_NO_BUFFER)
            gss_release_buffer(&c_min_stat, &server_tok);
        if (client_tok.length == 0)
            break;
        s_stat = gss_accept_sec_context(&s_min_stat, &server_ctx,
                                        GSS_C_NO_CREDENTIAL, &client_tok,
                                        GSS_C_NO_CHANNEL_BINDINGS,
                                        &client_name, &doid, &server_tok,
                                        &ret_flags, NULL, NULL);
        gss_release_buffer(&c_min_stat, &client_tok);
        if (server_tok.length == 0)
            break;
        token_ptr = &server_tok;
    } while (c_stat == GSS_S_CONTINUE_NEEDED
             || s_stat == GSS_S_CONTINUE_NEEDED);
    if (c_stat != GSS_S_COMPLETE || s_stat != GSS_S_COMPLETE)
        bail("cannot establish context");

    /* Okay, we should now be able to send and receive a token. */
    server_tok.value = (char *) "hello";
    server_tok.length = 5;
    status = token_send_priv(0, server_ctx, 3, &server_tok, &s_stat,
                             &s_min_stat);
    is_int(TOKEN_OK, status, "sent a token successfully");
    is_int(3, send_flags, "...with the right flags");
    ok(send_length > 5, "...and enough length");
    server_tok.value = send_buffer;
    server_tok.length = send_length;
    c_stat = gss_unwrap(&c_min_stat, client_ctx, &server_tok, &client_tok,
                        NULL, NULL);
    is_int(GSS_S_COMPLETE, c_stat, "...and it unwrapped");
    is_int(5, client_tok.length, "...with the right length");
    ok(memcmp(client_tok.value, "hello", 5) == 0, "...and contents");
    gss_release_buffer(&c_min_stat, &client_tok);
    client_tok.length = 0;
    client_tok.value = NULL;
    server_tok.value = (char *) "hello";
    server_tok.length = 5;
    status = token_send_priv(0, server_ctx, 3, &server_tok, &s_stat,
                             &s_min_stat);
    is_int(TOKEN_OK, status, "sent another token");
    memcpy(recv_buffer, send_buffer, send_length);
    recv_length = send_length;
    recv_flags = send_flags;
    status = token_recv_priv(0, client_ctx, &flags, &client_tok, 1024,
                             &s_stat, &c_min_stat);
    is_int(TOKEN_OK, status, "received the token");
    is_int(5, client_tok.length, "...with the right length");
    ok(memcmp(client_tok.value, "hello", 5) == 0, "...and the right data");
    is_int(3, flags, "...and the right flags");
    gss_release_buffer(&c_min_stat, &client_tok);

    /* Test receiving too large of a token. */
    status = token_recv_priv(0, client_ctx, &flags, &client_tok, 4, &s_stat,
                             &s_min_stat);
    is_int(TOKEN_FAIL_LARGE, status, "receiving too large of a token");

    /* Test receiving a corrupt token. */
    recv_length = 4;
    status = token_recv_priv(0, client_ctx, &flags, &client_tok, 1024,
                             &s_stat, &s_min_stat);
    is_int(TOKEN_FAIL_GSSAPI, status, "receiving a corrupt token");

    /*
     * Now, fake up a token to make sure that token_recv_priv is doing the
     * right thing.
     */
    recv_flags = 5;
    client_tok.value = (char *) "hello";
    client_tok.length = 5;
    c_stat = gss_wrap(&c_min_stat, client_ctx, 1, GSS_C_QOP_DEFAULT,
                      &client_tok, NULL, &server_tok);
    is_int(GSS_S_COMPLETE, c_stat, "wrapped a fake token");
    recv_length = server_tok.length;
    memcpy(recv_buffer, server_tok.value, server_tok.length);
    gss_release_buffer(&c_min_stat, &server_tok);
    status = token_recv_priv(0, server_ctx, &flags, &server_tok, 1024,
                             &s_stat, &s_min_stat);
    is_int(TOKEN_OK, status, "received a fake token");
    is_int(5, flags, "...with the right flags");
    is_int(5, server_tok.length, "...and the right length");
    ok(memcmp(server_tok.value, "hello", 5) == 0, "...and data");
    gss_release_buffer(&c_min_stat, &server_tok);

    /* Test the stupid protocol v1 MIC stuff. */
    server_tok.value = (char *) "hello";
    server_tok.length = 5;
    c_stat = gss_get_mic(&c_min_stat, client_ctx, GSS_C_QOP_DEFAULT,
                         &server_tok, &client_tok);
    is_int(GSS_S_COMPLETE, c_stat, "got MIC for protocol v1 token");
    memcpy(recv_buffer, client_tok.value, client_tok.length);
    recv_length = client_tok.length;
    recv_flags = TOKEN_MIC;
    status = token_send_priv(0, server_ctx, TOKEN_DATA | TOKEN_SEND_MIC,
                             &server_tok, &s_stat, &s_min_stat);
    is_int(TOKEN_OK, status, "sent protocol v1 token with MIC");
    memcpy(recv_buffer, send_buffer, send_length);
    recv_length = send_length;
    recv_flags = send_flags;
    status = token_recv_priv(0, client_ctx, &flags, &client_tok, 1024,
                             &c_stat, &c_min_stat);
    is_int(TOKEN_OK, status, "received protocol v1 token with MIC");
    is_int(TOKEN_DATA, flags, "...with the right flags");
    is_int(5, client_tok.length, "...and the right length");
    ok(memcmp(client_tok.value, "hello", 5) == 0, "...and the right data");
    is_int(TOKEN_MIC, send_flags, "...and the right send flags");
    server_tok.value = send_buffer;
    server_tok.length = send_length;
    s_stat = gss_verify_mic(&s_min_stat, server_ctx, &client_tok, &server_tok,
                            NULL);
    is_int(GSS_S_COMPLETE, s_stat, "...and would send correct MIC");

    return 0;
}
