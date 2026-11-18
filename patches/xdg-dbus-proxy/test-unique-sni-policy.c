/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include "flatpak-proxy.c"

int
main (void)
{
  FlatpakProxyClient client = { 0 };
  client.proxy = flatpak_proxy_new ("unix:path=/unused", "/unused");
  client.unique_id_policy = g_hash_table_new (g_str_hash, g_str_equal);
  client.unique_id_owned_names = g_hash_table_new (g_str_hash, g_str_equal);

  flatpak_proxy_add_call_rule (client.proxy, ":1.42", FALSE,
                               "org.freedesktop.DBus.Properties.GetAll@/StatusNotifierItem");
  /* A GetNameOwner reply for a unique name returns that name itself. The
   * startup alias table must never hold this recursive edge. */
  flatpak_proxy_client_add_unique_id_owned_name (&client, ":1.42", ":1.42");
  g_assert_null (g_hash_table_lookup (client.unique_id_owned_names, ":1.42"));
  Header message = {
    .type = G_DBUS_MESSAGE_TYPE_METHOD_CALL,
    .destination = ":1.42",
    .path = "/StatusNotifierItem",
    .interface = "org.freedesktop.DBus.Properties",
    .member = "GetAll",
  };
  g_assert_cmpint (get_dbus_method_handler (&client, &message), ==, HANDLE_PASS);

  message.destination = ":1.43";
  g_assert_cmpint (get_dbus_method_handler (&client, &message), ==, HANDLE_HIDE);
  message.destination = ":1.42";
  message.path = "/Other";
  g_assert_cmpint (get_dbus_method_handler (&client, &message), ==, HANDLE_DENY);
  message.path = "/StatusNotifierItem/Child";
  g_assert_cmpint (get_dbus_method_handler (&client, &message), ==, HANDLE_DENY);
  message.path = "/StatusNotifierItem";
  message.member = "Set";
  g_assert_cmpint (get_dbus_method_handler (&client, &message), ==, HANDLE_DENY);
  message.interface = "org.kde.StatusNotifierItem";
  message.member = "Activate";
  g_assert_cmpint (get_dbus_method_handler (&client, &message), ==, HANDLE_DENY);

  flatpak_proxy_add_broadcast_rule (client.proxy, ":1.42", FALSE,
                                   "org.kde.StatusNotifierItem.NewStatus@/StatusNotifierItem");
  flatpak_proxy_add_broadcast_rule (client.proxy, ":1.42", FALSE,
                                   "org.kde.StatusNotifierItem.NewIcon@/StatusNotifierItem");
  Header signal = {
    .type = G_DBUS_MESSAGE_TYPE_SIGNAL,
    .sender = ":1.42",
    .path = "/StatusNotifierItem",
    .interface = "org.kde.StatusNotifierItem",
    .member = "NewStatus",
  };
  g_assert_true (broadcast_allowed (&client, &signal));
  signal.member = "NewIcon";
  g_assert_true (broadcast_allowed (&client, &signal));
  signal.path = "/StatusNotifierItem/Child";
  g_assert_false (broadcast_allowed (&client, &signal));
  signal.path = "/StatusNotifierItem";
  signal.sender = ":1.43";
  g_assert_false (broadcast_allowed (&client, &signal));
  signal.sender = ":1.42";
  signal.member = "NewMenu";
  g_assert_false (broadcast_allowed (&client, &signal));
  message.member = "NewIcon";
  g_assert_cmpint (get_dbus_method_handler (&client, &message), ==, HANDLE_DENY);

  g_hash_table_unref (client.unique_id_owned_names);
  g_hash_table_unref (client.unique_id_policy);
  g_object_unref (client.proxy);
  return 0;
}
