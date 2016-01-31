var msparp = (function() {

	var body = $(document.body);

	// Remember toggle box state
	$(".toggle_box > input:first-child").change(function() {
		if (this.id) { localStorage.setItem(this.id, this.checked); }
	}).each(function() {
		if (this.id && !this.checked) { this.checked = localStorage.getItem(this.id) == "true"; }
	});

	// Character info
	function update_character(data) {
		if (typeof data["search_character"]!= "undefined") {
			$("[name=search_character_id]").val(data["search_character"]["id"]);
		} else {
			$("[name=search_character_id]").val(data["id"]);
		}
		$("#toggle_with_settings").prop("checked", true).change();
		$("input[name=name]").val(data["name"]);
		$("input[name=acronym]").val(data["acronym"]).keyup();
		$("input[name=color]").val("#"+data["color"]).change();
		if (!body.hasClass("chat")) {
			if (typeof data["text_preview"]!= "undefined") {
				$("#text_preview").text(data["text_preview"]);
			} else if (typeof data["search_character"]!= "undefined") {
				$("#text_preview").text(data["search_character"]["text_preview"]);
			}
		}
		if (data["quirk_prefix"] != "" || data["quirk_suffix"] != "" || data["case"] != "normal" || data["replacements"].length != 0 || data["regexes"].length != 0) {
			$("#toggle_typing_quirks").prop("checked", true).change();
		}
		$("input[name=quirk_prefix]").val(data["quirk_prefix"]);
		$("input[name=quirk_suffix]").val(data["quirk_suffix"]);
		$("select[name=case]").val(data["case"]);
		clear_replacements();
		if (data["replacements"].length == 0) {
			add_replacement();
		} else {
			data["replacements"].forEach(function(replacement) { add_replacement(null, replacement[0], replacement[1]); });
		}
		clear_regexes();
		if (data["regexes"].length == 0) {
			add_regex();
		} else {
			data["regexes"].forEach(function(regex) { add_regex(null, regex[0], regex[1]); });
		}
	}

	// Replacement list
	function delete_replacement(e) {
		if (this.parentNode.parentNode.childElementCount == 1) {
			add_replacement();
		}
		$(this.parentNode).remove();
		return false;
	}
	function add_replacement(e, from, to) {
		var size = body.hasClass("chat") ? 7 : 10;
		new_item = $("<li><input type=\"text\" name=\"quirk_from\" size=\"" + size + "\"> to <input type=\"text\" name=\"quirk_to\" size=\"" + size + "\"> <button type=\"button\" class=\"delete_replacement\">x</button></li>");
		if (from || to) {
			var inputs = $(new_item).find('input');
			inputs[0].value = from;
			inputs[1].value = to;
		}
		$(new_item).find('.delete_replacement').click(delete_replacement);
		$(new_item).appendTo('#replacement_list');
		return false;
	}
	function clear_replacements(e) {
		$('#replacement_list').empty();
		return false;
	}
	function clear_replacements_and_add(e) {
		$('#replacement_list').empty();
		add_replacement();
		return false;
	}

	// Regex list
	function delete_regex(e) {
		if (this.parentNode.parentNode.childElementCount == 1) {
			add_regex();
		}
		$(this.parentNode).remove();
		return false;
	}
	function add_regex(e, from, to) {
		var size = body.hasClass("chat") ? 7 : 10;
		new_item = $("<li><input type=\"text\" name=\"regex_from\" size=\"" + size + "\"> to <input type=\"text\" name=\"regex_to\" size=\"" + size + "\"> <button type=\"button\" class=\"delete_regex\">x</button></li>");
		if (from && to) {
			var inputs = $(new_item).find('input');
			inputs[0].value = from;
			inputs[1].value = to;
		}
		$(new_item).find('.delete_regex').click(delete_regex);
		$(new_item).appendTo('#regex_list');
		return false;
	}
	function clear_regexes(e) {
		$('#regex_list').empty();
		return false;
	}
	function clear_regexes_and_add(e) {
		$('#regex_list').empty();
		add_regex();
		return false;
	}

	// Event handlers for character form
	function initialize_character_form() {
		// Search character dropdown
		$("select[name=search_character_id]").change(function() {
			$.get("/search_characters/"+this.value+".json", {}, update_character);
		});
		$("select[name=id]").change(function() {
			var url = this.value[0] == "s" ? "search_characters" : "characters";
			$.get("/" + url + "/" + this.value.substr(2) + ".json", {}, update_character);
		});
		// Text preview
		var text_preview_container = $("#text_preview_container");
		var text_preview_acronym = $("#text_preview_acronym");
		$("input[name=acronym]").keyup(function() {
			if (this.value == "") {
				text_preview_acronym.text("");
			} else {
				text_preview_acronym.text(this.value + ": ");
			}
		});
		// Color and color_hex
		var color_input = $("input[name=color]").change(function() {
			color_hex_input.val(this.value.substr(1));
			text_preview_container.css("color", this.value);
		});
		var color_hex_input = $("#color_hex_input").keyup(function() {
			if (this.value.length == 6) {
				color_input.val("#" + this.value);
				text_preview_container.css("color", "#" + this.value);
			}
		});
		// Replacement list
		$('.delete_replacement').click(delete_replacement);
		$('#add_replacement').click(add_replacement);
		$('#clear_replacements').click(clear_replacements_and_add);
		// Regex list
		$('.delete_regex').click(delete_regex);
		$('#add_regex').click(add_regex);
		$('#clear_regexes').click(clear_regexes_and_add);
	}

	// Searching
	var search_type = "search"
	var searching = false;
	var searcher_id;

	function start_search() {
		if (!searching) {
			searching = true;
			body.addClass("searching");
			$.post("/" + search_type, {}, function(data) {
				searcher_id = data.id;
				continue_search();
			}).error(function() {
				searching = false;
				body.removeClass("searching").addClass("search_error");
			});
		}
	}
	function continue_search() {
		if (searching) {
			$.post("/" + search_type + "/continue", { "id": searcher_id }, function(data) {
				if (data.status == "matched") {
					searching = false;
					window.location.href = "/" + data.url;
				} else if (data.status == "quit") {
					searching = false;
				} else {
					continue_search();
				}
			}).error(function() {
				window.setTimeout(function() {
					searching = false;
					start_search();
				}, 2000);
			});
		}
	}
	function stop_search() {
		searching = false;
		$.ajax("/" + search_type + "/stop", { "type": "POST", data: { "id": searcher_id }, "async": false });
		body.removeClass("searching");
	}

	// BBCode
	var tag_properties = {bgcolor: "background-color", color: "color", font: "font-family", bshadow: "box-shadow", tshadow: "text-shadow"}
	function bbencode(text, admin) { return raw_bbencode(Handlebars.escapeExpression(text), admin); }
	function raw_bbencode(text, admin) {
		text = text.replace(/(\[br\])+/g, "<br>");
		return text.replace(/(https?:\/\/\S+)|\[([A-Za-z]+)(?:=([^\]]+))?\]([\s\S]*?)\[\/\2\]/g, function(str, url, tag, attribute, content) {
			if (url) {
				var suffix = "";
				// Exclude a trailing closing bracket if there isn't an opening bracket.
				if (url[url.length - 1] == ")" && url.indexOf("(") == -1) {
					url = url.substr(0, url.length-1);
					suffix = ")";
				}
				return $("<a>").attr({href: url, target: "_blank"}).text(url)[0].outerHTML + suffix;
			}
			tag = tag.toLowerCase();
			if (attribute) {
				switch (tag) {
					case "bgcolor":
					case "color":
					case "font":
						return $("<span>").css(tag_properties[tag], attribute).html(raw_bbencode(content, admin))[0].outerHTML;
					case "bshadow":
					case "tshadow":
						return admin ? $("<span>").css(tag_properties[tag], attribute).html(raw_bbencode(content, admin))[0].outerHTML : raw_bbencode(content, admin);
					case "url":
						if (attribute.substr(0, 7) == "http://" || attribute.substr(0, 8) == "https://") {
							return $("<a>").attr({href: attribute, target: "_blank"}).html(raw_bbencode(content, admin))[0].outerHTML;
						}
						break;
				}
			} else {
				switch (tag) {
					case "b":
					case "del":
					case "i":
					case "sub":
					case "sup":
					case "u":
					case "s":
						return "<" + tag + ">" + raw_bbencode(content, admin) + "</" + tag + ">";
					case "spoiler":
						return "<label class=\"spoiler\"><input type=\"checkbox\"><span>SPOILER</span> <span>" + raw_bbencode(content, admin) + "</span></label>";
					case "raw":
						return content;
				}
			}
			return "[" + tag + (attribute ? "=" + attribute : "") + "]" + raw_bbencode(content, admin) + "[/" + tag + "]";
		});
	}
	function bbremove(text) {
		text = text.replace(/(\[br\])+/g, "");
		return text.replace(/\[([A-Za-z]+)(?:=[^\]]+)?\]([\s\S]*?)\[\/\1\]/g, function(str, tag, content) { return bbremove(content); });
	}

	// Workers
	function init_notifications() {
		Notification.requestPermission(function(state) {
			if (state === "granted") {
				init_push();
			}
		});
	}

	function init_push() {
		if (!("serviceWorker" in navigator)) return;

		navigator.serviceWorker.ready.then(function(registration) {
			registration.pushManager.getSubscription().then(function(subscription) {
				// Do nothing if we already are subscribed to pushs.
				if (subscription) {
					navigator.serviceWorker.controller.postMessage({
						action: "subscription",
						subscription: {endpoint: subscription.endpoint}
					});
					return;
				}

				registration.pushManager.subscribe({
					userVisibleOnly: true
				}).then(function(subscription) {
					navigator.serviceWorker.controller.postMessage({
						action: "subscription",
						subscription: {endpoint: subscription.endpoint}
					});
				}).catch(function(e) {
					console.error("Push Register:", e);
				});
			});
		});
	}

	if ("serviceWorker" in navigator) {
		navigator.serviceWorker.register("/service_worker.js", { scope: "/" }).catch(function(e) {
			console.error("Error registering worker:", e);
		});
	}

	return {
		// Registration
		"register": function() {
			$("#register_show_password_input").change(function(e) {
				$("#register_password_input, #register_password_again_input").attr("type", this.checked ? "text" : "password");
			});
		},
		// Logging in
		"log_in": function() {
			$("#log_in_show_password_input").change(function(e) {
				$("#log_in_password_input").attr("type", this.checked ? "text" : "password");
			});
		},
		// Homepage
		"home": function() {

			// Saved character dropdown
			$("select[name=character_id]").change(function() {
				if (this.value != "") {
					$.get("/characters/"+this.value+".json", {}, update_character);
				}
			});

			initialize_character_form();

			// Filter list
			function delete_filter(e) {
				if (this.parentNode.parentNode.childElementCount == 1) {
					add_filter();
				}
				$(this.parentNode).remove();
				return false;
			}
			function add_filter() {
				new_item = $("<li><input type=\"text\" name=\"search_filter\" size=\"25\" maxlength=\"50\"> <button type=\"button\" class=\"delete_filter\">x</button></li>");
				$(new_item).find('.delete_filter').click(delete_filter);
				$(new_item).appendTo('#filter_list');
				return false;
			}
			function clear_filters(e) {
				$('#filter_list').empty();
				return false;
			}
			function clear_filters_and_add(e) {
				$('#filter_list').empty();
				add_filter();
				return false;
			}
			$('.delete_filter').click(delete_filter);
			$('#add_filter').click(add_filter);
			$('#clear_filters').click(clear_filters_and_add);

			// Picky checkboxes
			$(".character_list legend input").click(function() {
				var group = $(this).parentsUntil(".toggle_box").last();
				group.find("li input").prop("checked", this.checked);
			});
			$(".character_list ul input").click(function() {
				var group = $(this).parentsUntil(".toggle_box").last();
				var group_input = group.find("legend input");
				var characters = group.find("li input");
				var checked_characters = group.find("li input:checked");
				if (checked_characters.length == 0) {
					group_input.prop("checked", false).prop("indeterminate", false);
				} else if (checked_characters.length == characters.length) {
					group_input.prop("checked", true).prop("indeterminate", false);
				} else {
					group_input.prop("checked", false).prop("indeterminate", true);
				}
			});

		},
		// Character search
		"search": function(token) {
			$.ajaxSetup({data: {"token": token}});
			$(window).unload(function () { if (searching) { stop_search(); }});
			start_search();
		},
		// Roulette
		"roulette": function(token) {
			$.ajaxSetup({data: {"token": token}});
			search_type = "roulette";
			$(window).unload(function () { if (searching) { stop_search(); }});
			start_search();
		},
		// Character pages
		"character": function() {
			initialize_character_form();
			var shortcut_preview = $("#shortcut_preview");
			$("#shortcut_input").keyup(function() {
				var new_shortcut = this.value.trim();
				shortcut_preview.text(new_shortcut ? "\"/" + this.value + "\"" : "the shortcut");
			});
		},
		// Search character pages
		"search_character": function() {
			initialize_character_form();
			$("#text_preview_input").keyup(function() { $("#text_preview").text(this.value); });
		},
		// Settings: log in details
		"settings_log_in_details": function() {
			$("#change_password_show_password").change(function(e) {
				$("#change_password_old_password, #change_password_new_password, #change_password_new_password_again").attr("type", this.checked ? "text" : "password");
			});
		},
		// Chat window
		"chat": function(chat, user, character_shortcuts, latest_message_id, latest_time, token) {

			$.ajaxSetup({data: {"token": token}});

			var conversation = $("#conversation");
			var status;
			var next_chat_url;
			var user_data = {};
			var latest_date = user.meta.show_timestamps ? new Date(latest_time * 1000) : null;
			var new_messages = [];

			// Websockets
			var messages_method = typeof(WebSocket) != "undefined" ? "websocket" : "long_poll";
			var ws_protocol = (location.protocol=="https:") ? "wss://" : "ws://";
			var ws;
			var ws_works = false;
			var ws_connected_time = 0;
			function launch_websocket() {
				// Don't create a new websocket unless the previous one is closed.
				// This prevents problems with eg. double clicking the join button.
				if (ws && ws.readyState != 3) { return; }
				status = "connecting";

				ws = new WebSocket(ws_protocol + "live." + location.host + "/" + chat.id + "?after=" + latest_message_id);
				ws.onopen = function(e) { ws_works = true; ws_connected_time = Date.now(); enter(); }
				ws.onmessage = function(e) { receive_messages(JSON.parse(e.data)); }
				ws.onclose = function(e) {
					if (status == "connecting" || status == "chatting") {
						// Fall back to long polling if we've never managed to connect.
						if (!ws_works || (Date.now() - ws_connected_time) < 5000) {
							messages_method = "long_poll";
							launch_long_poll(true);
							return;
						}
						// Otherwise try to reconnect.
						exit();
						status_bar.css("color", "#f00").text("Sorry, the connection to the server has been lost. Attempting to reconnect...");
						window.setTimeout(launch_websocket, 2000);
					}
				}
			}

			// Long polling
			function launch_long_poll(joining) {
				var data = { "chat_id": chat.id, "after": latest_message_id };
				if (joining) { enter(); data["joining"] = true; }
				$.post("/chat_api/messages", data, receive_messages).complete(function(jqxhr, text_status) {
					if (status == "chatting") {
						if (jqxhr.status < 400 && text_status == "success") {
							launch_long_poll();
						} else {
							window.setTimeout(launch_long_poll, 2000);
							// XXX display a message if it still doesn't work after several attempts.
						}
					}
				});
			}

			// Ping loop
			function ping() {
				if (status == "chatting") {
					if (messages_method == "websocket") {
						if (ws.readyState == 1) {
							ws.send("ping");
							window.setTimeout(ping, 10000);
						}
					} else {
						$.post("/chat_api/ping", { "chat_id": chat.id }).complete(function() { window.setTimeout(ping, 10000); });
					}
				}
			}

			// Connecting and disconnecting
			function connect() {
				if (messages_method == "websocket") {
					launch_websocket();
				} else {
					launch_long_poll(true);
				}
			}
			function enter() {
				status = "chatting";
				window.setTimeout(ping, 10000);
				$("#disconnect_links").appendTo(document.body);
				body.addClass("chatting");
				set_sidebar(null);
				if (chat.type == "pm") { refresh_pm_chat_list(); }
				$("#send_form input, #send_form button").prop("disabled", false);
				set_temporary_character(null);
				parse_variables();
				status_bar.css("color", "").text((
					// Show status bar if typing notifications are available and switched on.
					(messages_method == "websocket" && user.meta.typing_notifications)
					// Also always show it in PM and roulette chats for online status.
					|| chat.type == "pm" || chat.type == "roulette"
				) ? " " : "");
				text_input.keyup();
				scroll_to_bottom();
				abscond_button.text("Abscond");
				$("#messages_method").text(messages_method);
			}
			function exit() {
				status = "disconnected";
				body.removeClass("chatting");
				$("#send_form input, #send_form button:not(#abscond_button)").prop("disabled", true);
				if (chat.type == "group") {
					info_panel.hide();
					edit_info_panel.hide();
				}
				set_sidebar(null);
				status_bar.text("");
				abscond_button.text(chat.type == "searched" || chat.type == "roulette" ? "Search again" : "Join");
			}
			function disconnect() {
				exit();
				if (messages_method == "websocket") {
					ws.close(); receive_messages({});
				} else {
					$.ajax("/chat_api/quit", { "type": "POST", data: { "chat_id": chat.id } });
				}
			}

			// Quitting
			window.onbeforeunload = function(e) {
				if (status == "chatting" && user.meta.confirm_disconnect) {
					if (typeof e != "undefined") { e.preventDefault(); }
					return "";
				}
			}
			$(window).unload(function() {
				if (status == "chatting") {
					status = "disconnected";
					if (messages_method != "websocket") {
						$.ajax("/chat_api/quit", { "type": "POST", data: { "chat_id": chat.id }, "async": false });
					}
				}
			});

			// Parsing and rendering messages
			var show_notification = false;
			function receive_messages(data) {
				if (typeof data.exit != "undefined") {
					exit();
					if (data.exit == "kick") {
						render_message({
							"acronym": "",
							"color": "000000",
							"id": null,
							"name": "",
							"posted": Math.floor(Date.now() / 1000),
							"text": "You have been kicked from this chat. Please think long and hard about your behavior before returning.",
							"type": "exit",
							"user_number": null,
						});
						scroll_to_bottom();
					} else if (data.exit == "ban") {
						if (chat.url != "theoubliette") { location.replace("/theoubliette") };
					}
					return;
				}
				if (typeof data.chat != "undefined" && chat.type != "pm") {
					chat = data.chat;
					if (chat.type == "group") {
						topic.text(chat.topic);
						if (user.meta.show_bbcode) {
							description.html(bbencode(chat.description, false));
							rules.html(bbencode(chat.rules, false));
						} else {
							description.text(bbremove(chat.description));
							rules.text(bbremove(chat.rules));
						}
						flag_autosilence.prop("checked", chat.autosilence);
						if (chat.publicity == "pinned" && user.meta.group != "admin") {
							flag_publicity.val("listed");
							flag_publicity.prop("disabled", true);
						} else {
							flag_publicity.val(chat.publicity);
							flag_publicity.prop("disabled", false);
						}
						chat.publicity == "private" ? invites_link.show() : invites_link.hide();
						flag_style.val(chat.style);
						flag_level.val(chat.level);
						chat.autosilence ? flag_message_autosilence.show() : flag_message_autosilence.hide();
						chat.publicity == "listed" || chat.publicity == "pinned" ? flag_message_publicity.show() : flag_message_publicity.hide();
						flag_message_style.text(style_messages[chat.style]);
						flag_message_level.text(level_names[chat.level]);
					}
				}
				if (typeof data.users != "undefined") {
					var others_online = false;
					for (var i = 0; i < data.users.length; i++) {
						// Store user data so we can look it up for action lists.
						user_data[data.users[i].meta.number] = data.users[i];
						// Also handle group changes.
						if (data.users[i].meta.number == user.meta.number) {
							user.meta.group = data.users[i].meta.group;
							if (chat.type == "group") {
								if (user.meta.group == "admin" || user.meta.group == "creator" || user.meta.group == "mod3" || user.meta.group == "mod2" || user.meta.group == "mod1") {
									mod_tools.show();
									info_panel_controls.show();
									flag_messages.hide();
								} else {
									mod_tools.hide();
									info_panel_controls.hide();
									flag_messages.show();
								}
							}
							if (user.meta.group == "silent") {
								text_input.prop("disabled", true);
								send_button.prop("disabled", true);
							} else {
								text_input.prop("disabled", false);
								send_button.prop("disabled", false);
							}
						} else {
							others_online = true;
						}
					}
					if (chat.type == "pm" || chat.type == "roulette") {
						var status_message = (chat.type == "pm" ? chat.url.substr(3) : "▼") + " is " + (others_online ? "online." : "offline.");
						if (previous_status_message) {
							previous_status_message = status_message;
						} else {
							status_bar.text(status_message);
						}
					} else {
						user_list.html(user_list_template(data));
						user_list.find("li").click(render_action_list);
						// Re-render the action list if necessary.
						if (action_user != null) {
							var action_user_number = action_user.meta.number;
							var action_user_li = user_list.find("#unum_" + action_user_number);
							// Set to null so it fires the open action rather than the close action.
							if (action_user_li.length != 0) {
								action_user = null;
								action_user_li.click();
							}
						}
					}
				}
				if (typeof data.messages != "undefined" && data.messages.length != 0) {
					var scroll_after_render = is_at_bottom();
					data.messages.forEach(render_message);
					if (scroll_after_render) { scroll_to_bottom(); }
				}
				if (typeof data.delete != "undefined" && data.delete.length != 0) {
					data.delete.forEach(function(id) {
						console.log("delete " + id);
						$("#message_" + id).remove();
						// Remove "New messages" text if this was the only message.
						if (new_messages.length > 0) {
							var index = new_messages.indexOf(id);
							if (index != -1) { new_messages.splice(index, 1); }
							if (new_messages.length == 0) { document.title = original_title; }
						}
					});
				}
				if (user.meta.typing_notifications && typeof data.typing != "undefined") {
					if (data.typing.length == 0 || (data.typing.length == 1 && data.typing.indexOf(user.meta.number) == 0)) {
						if (previous_status_message) {
							status_bar.text(previous_status_message);
							previous_status_message = null;
						}
					} else {
						if (!previous_status_message) { previous_status_message = status_bar.text(); }
						var name = chat.type == "pm" ? chat.url.substr(3) : chat.type == "roulette" ? "▼" : "Someone";
						status_bar.text(name + " is typing...");
					}
				}
				if (chat.type == "pm" && typeof data.pm != "undefined") {
					refresh_pm_chat_list();
				}
				if (status == "disconnected") {
					if (next_chat_url) {
						$.get("/" + next_chat_url + ".json", {}, function(data) {
							chat = data.chat;
							document.title = chat.title + " - MSPARP";
							history.replaceState({}, chat.url, "/" + chat.url);
							user = data.chat_user;
							latest_message_id = data.latest_message_id;
							conversation.html("<p><a href=\"/" + chat.url + "/log\" target=\"_blank\">View log</a></p>");
							status_bar = $("<p>").attr("id", "status_bar").appendTo(conversation);
							data.messages.forEach(render_message);
							connect();
						});
						next_chat_url = null;
					} else {
						$("#disconnect_links").appendTo(conversation);
						scroll_to_bottom();
					}
				}
			}
			function render_message(message) {
				// XXX yeah you should be using a template here
				// Use initial setting for consistency.
				if (latest_date) {
					message_date = new Date(message.posted * 1000);
					if (latest_date.getDate() != message_date.getDate() || latest_date.getMonth() != message_date.getMonth() || latest_date.getFullYear() != message_date.getFullYear()) {
						$("<h2>").text(message_date.toDateString()).insertBefore(status_bar);
					}
					latest_date = message_date;
				}
				var div = $("<div>");
				if (message.id) {
					latest_message_id = message.id;
					div.attr("id", "message_" + message.id);
				}
				div.addClass("message_" + message.type + " unum_" + message.user_number);
				$("<div>").addClass("unum").text("[" + (message.user_number ? message.user_number : "*") + "]").appendTo(div);
				var p = $("<p>").css("color", "#" + message.color);
				if (message.type == "me") {
					var text = "* " + message.name + " " + message.text;
				} else if (chat.type == "roulette" && ["ic", "ooc"].indexOf(message.type) != -1) {
					var text = (message.user_number == user.meta.number ? "▲" : "▼") + ": " + message.text;
				} else if (message.acronym != "") {
					var text = message.acronym + ": " + message.text;
				} else {
					var text = message.text;
				}
				var admin = (message.user_number && user_data[message.user_number] && user_data[message.user_number].meta.group == "admin");
				user.meta.show_bbcode ? p.html(bbencode(text, admin)) : p.text(bbremove(text));
				if (chat.type == "searched" && (message.type == "disconnect" || message.type == "timeout") && message.user_number != user.meta.number) {
					$("<a>").attr("href", "#").addClass("message_action").text("Block").click(function() { block(message.user_number); return false; }).appendTo(p);
				} else if (message.type == "user_group" && ranks[user.meta.group] >= ranks["mod3"] && user_data[message.user_number] && user_data[message.user_number].meta.group == "silent") {
					$("<a>").attr("href", "#").addClass("message_action").text("Unsilence").click(function() {
						if (user_data[message.user_number].meta.group == "silent") { set_group(message.user_number, "user"); }
						return false;
					}).appendTo(p);
				} else if (message.type == "user_action" && ranks[user.meta.group] >= ranks["mod3"] && message.text.indexOf("] banned ") != -1) {
					$("<a>").attr("href", "#").addClass("message_action").text("Unban").click(function() {
						$.post("/" + chat.url + "/unban", {"number": message.user_number});
						return false;
					}).appendTo(p);
				} else if (message.type == "username_request") {
					$("<a>").attr("href", "#").addClass("message_action").text("Allow").click(function() {
						$.post("/chat_api/exchange_usernames", {"chat_id": chat.id, "number": message.user_number});
						$(this.parentNode.parentNode).remove();
						return false;
					}).appendTo(p);
					$("<a>").attr("href", "#").addClass("message_action").text("Deny").click(function() {
						$(this.parentNode.parentNode).remove();
						return false;
					}).appendTo(p);
				}
				if (latest_date) {
					$("<time>").addClass("timestamp").text(message_date.toLocaleTimeString()).appendTo(p);
				}
				p.appendTo(div);
				if (message.user_number && user.meta.highlighted_numbers.indexOf(message.user_number) != -1) { div.addClass("highlighted"); }
				if (message.user_number && user.meta.ignored_numbers.indexOf(message.user_number) != -1) { div.addClass("ignored"); }
				div.insertBefore(status_bar);

				// Post all global messages as a notification banner.
				if (message.type.indexOf("global") !== -1 && message.important) {
					announcement_banner(message.title, message.text);
				}

				if (
					(document.hidden || document.webkitHidden || document.msHidden)
					// Skip notifications for system messages if we're hiding them.
					&& (user.meta.show_system_messages || ["ic", "ooc", "me", "global", "spamless"].indexOf(message.type) != -1)
					// Skip notifications if we're ignoring this person.
					&& user.meta.ignored_numbers.indexOf(message.user_number) == -1
				) {
					new_messages.push(message.id);
					document.title = "New message - " + original_title;
					if (user.meta.desktop_notifications && typeof Notification != "undefined") {
						var text_without_bbcode = bbremove(text);
						var notification = new Notification(chat.title || "MSPARP", {
							"body": text_without_bbcode.length <= 50 ? text_without_bbcode : text_without_bbcode.substr(0, 47) + "...",
							"icon": "/static/img/spinner-big.png"
						});

						notification.onclick = function() {
							window.focus();
							this.close();
						}

						window.setTimeout(notification.close.bind(notification), 5000);
					}
				}
			}

			// "New message" notification
			var original_title = document.title;
			function visibility_handler() {
				window.setTimeout(function() { new_messages = []; document.title = original_title; }, 200);
			}
			if (typeof document.hidden !== "undefined") {
				document.addEventListener("visibilitychange", visibility_handler);
			} else if (typeof document.msHidden !== "undefined") {
				document.addEventListener("msvisibilitychange", visibility_handler);
			} else if (typeof document.webkitHidden !== "undefined") {
				document.addEventListener("webkitvisibilitychange", visibility_handler);
			}

			// Names and text
			var style_messages = {
				"script": "Please use script style.",
				"paragraph": "Please use paragraph style.",
				"either": "Script and paragraph style are allowed.",
			};
			var level_names = { "sfw": "SFW", "nsfw": "NSFW", "nsfw-extreme": "NSFW extreme" };
			var group_descriptions = {
				"admin": "God tier moderator - MSPARP staff.",
				"creator": "Chat creator - can silence, kick and ban other users.",
				"mod3": "Professional Wet Blanket - can silence, kick and ban other users.",
				"mod2": "Bum's Rusher - can silence and kick other users.",
				"mod1": "Amateur Gavel-Slinger - can silence other users.",
				"user": "",
				"silent": "Silenced.",
			};

			// Actions and validation
			function can_block(their_number) {
				return (chat.type == "searched" || chat.type == "roulette") && their_number != user.meta.number;
			}
			function block(number) {
				var reason = prompt("If you block this person, you will never encounter them in random chats. Optionally, you can also provide a reason below.");
				if (reason == null) { return; }
				$.post("/chat_api/block", { "chat_id": chat.id, "number": number, "reason": reason });
			}
			function can_set_group(new_group, current_group) {
				// Setting group only works in group chats.
				if (chat.type != "group") { return false; }
				// Don't bother if they're already this group.
				if (ranks[new_group] == ranks[current_group]) { return false; }
				// You can't set groups at all if you're not a mod.
				if (ranks[user.meta.group] < 1) { return false; }
				// You can only set the group to one which is below yours.
				if (ranks[new_group] >= ranks[user.meta.group]) { return false; }
				// You can only set the group of people whose group is below yours.
				if (ranks[current_group] >= ranks[user.meta.group]) { return false; }
				return true;
			}
			function can_perform_action(action, their_group) {
				// User actions only work in group chats.
				if (chat.type != "group") { return false; }
				// You can only kick if you're a Bum's Rusher or above.
				if (action == "kick" && ranks[user.meta.group] < 2) { return false; }
				// You can only ban if you're a Bum's Rusher or above.
				if (action == "ban" && ranks[user.meta.group] < 3) { return false; }
				// You can only perform actions on people whose group is below yours.
				if (ranks[their_group] >= ranks[user.meta.group]) { return false; }
				return true;
			}
			if (chat.type == "group") {
				function set_group(number, group) { $.post("/chat_api/set_group", { "chat_id": chat.id, "number": number, "group": group }); }
				function user_action(number, action, reason) {
					var data = { "chat_id": chat.id, "number": number, "action": action };
					if (reason) { data["reason"] = reason; }
					$.post("/chat_api/user_action", data);
				}
			}

			// Text commands
			var text_commands = [
				{
					"regex": /^me (.*\S+.*)/,
					"chat_types": "all",
					"minimum_rank": 0,
					"description": function(match) {
						return "* " + user.character.name + " " + match[1];
					},
					"action": function(match) {
						$.post("/chat_api/send", { "chat_id": chat.id, "type": "me", "text": match[1] });
					},
				},
				{
					"regex": /^block (\d+)($|\s.*$)?/,
					"chat_types": "searched_and_roulette",
					"minimum_rank": 0,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || set_user.meta.number != user.meta.number) {
							if ((match[2] || "").trim().length > 500) { return "Block reasons can only be 500 characters long."; }
							return "Block " + name_from_user_number(parseInt(match[1])) + ". You will no longer encounter them in random chats.";
						} else {
							return "You can't block yourself.";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || set_user.meta.number != user.meta.number) {
							$.post("/chat_api/block", { "chat_id": chat.id, "number": match[1], "reason": (match[2] || "").trim() });
						}
					},
				},
				{
					"regex": /^username (\d+)$/,
					"chat_types": "all",
					"minimum_rank": 0,
					"description": function(match) {
						if (parseInt(match[1]) != user.meta.number) {
							return "Request " + name_from_user_number(parseInt(match[1])) + "'s username.";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (set_user && set_user.meta.number != user.meta.number) {
							$.post("/chat_api/request_username", { "chat_id": chat.id, "number": match[1] });
						}
					},
				},
				{
					"regex": /^topic($|\s.*$)/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						var new_topic = match[1].trim();
						if (new_topic.length > 500) { return "Topics can only be 500 characters long."; }
						return new_topic ? "Set the topic to \"" + new_topic + "\"" : "Remove the topic.";
					},
					"action": function(match) {
						$.post("/chat_api/set_topic", { "chat_id": chat.id, "topic": match[1].trim() });
					},
				},
				{
					"regex": /^set (\d+) (mod3|mod2|mod1|user|silent)$/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						var group_description = group_descriptions[match[2]] || "regular user.";
						if (!set_user || can_set_group(match[2], set_user.meta.group)) {
							return "Set " + name_from_user_number(parseInt(match[1])) + " to " + group_descriptions[match[2]];
						} else if (match[2] == set_user.meta.group) {
							return set_user.character.name + " is already a member of this group.";
						} else {
							return "Your current privileges don't allow you to set " + set_user.character.name + "'s group.";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_set_group(match[2], set_user.meta.group)) { set_group(match[1], match[2]); }
					},
				},
				{
					"regex": /^kick (\d+)$/,
					"chat_types": "group",
					"minimum_rank": 2,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("kick", set_user.meta.group)) {
							return "Kick " + name_from_user_number(parseInt(match[1])) + " from the chat.";
						} else {
							return "Your current privileges don't allow you to kick " + set_user.character.name + ".";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("kick", set_user.meta.group)) { user_action(match[1], "kick"); }
					},
				},
				{
					"regex": /^ban (\d+)($|\s.*$)?/,
					"chat_types": "group",
					"minimum_rank": 3,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("ban", set_user.meta.group)) {
							if ((match[2] || "").trim().length > 500) { return "Ban reasons can only be 500 characters long."; }
							return "Ban " + name_from_user_number(parseInt(match[1])) + " from the chat.";
						} else {
							return "Your current privileges don't allow you to ban " + set_user.character.name + ".";
						}
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						if (!set_user || can_perform_action("ban", set_user.meta.group)) { user_action(match[1], "ban", (match[2] || "").trim()); }
					},
				},
				{
					"regex": /^unban (\d+)?/,
					"chat_types": "group",
					"minimum_rank": 3,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						return "Unban " + name_from_user_number(parseInt(match[1])) + " from the chat.";
					},
					"action": function(match) {
						$.post("/" + chat.url + "/unban", {"number": parseInt(match[1])});
					},
				},
				{
					"regex": /^autosilence (on|off)/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						return "Switch autosilence " + match[1] + ".";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "autosilence", "value": match[1] });
					},
				},
				{
					"regex": /^publicity (private|listed|unlisted)/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						return "Set the publicity to " + match[1] + ".";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "publicity", "value": match[1] });
					},
				},
				{
					"regex": /^publicity pinned/,
					"chat_types": "group",
					"minimum_rank": Infinity,
					"description": function(match) {
						return "Set the publicity to pinned.";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "publicity", "value": "pinned" });
					},
				},
				{
					"regex": /^level (sfw|nsfw|nsfw-extreme)$/,
					"chat_types": "group",
					"minimum_rank": 1,
					"description": function(match) {
						return "Mark the chat as " + level_names[match[1]] + ".";
					},
					"action": function(match) {
						$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "level", "value": match[1] });
					},
				},
				{
					"regex": /^lookup (\d+)$/,
					"chat_types": "group",
					"minimum_rank": Infinity,
					"description": function(match) {
						var set_user = user_data[parseInt(match[1])];
						return "Look up " + name_from_user_number(parseInt(match[1])) + ".";
					},
					"action": function(match) {
						var set_user = user_data[parseInt(match[1])];
						$.post("/chat_api/look_up_user", { "chat_id": chat.id, "number": match[1] });
					},
				},
			];
			function name_from_user_number(number) {
				return user_data[number] ? user_data[number].character.name : "user " + number;
			}
			function get_command_description(text) {
				for (var i=0; i < text_commands.length; i++) {
					if (text_commands[i].chat_types == "group" && chat.type != "group") { continue; }
					if (text_commands[i].chat_types == "searched_and_roulette" && chat.type != "searched" && chat.type != "roulette") { continue; }
					if (text_commands[i].minimum_rank > ranks[user.meta.group]) { continue; }
					var match = text.match(text_commands[i].regex);
					if (match && match.length > 0) { return text_commands[i].description(match); }
				}
				return false;
			}
			function execute_command(text) {
				for (var i=0; i < text_commands.length; i++) {
					if (text_commands[i].chat_types == "group" && chat.type != "group") { continue; }
					if (text_commands[i].chat_types == "searched_and_roulette" && chat.type != "searched" && chat.type != "roulette") { continue; }
					if (text_commands[i].minimum_rank > ranks[user.meta.group]) { continue; }
					var match = text.match(text_commands[i].regex);
					if (match && match.length > 0) { text_commands[i].action(match); return true; }
				}
				return false;
			}

			// Temporary characters
			var temporary_character = null;
			function set_temporary_character(data) {
				temporary_character = data;
				text_preview.css("color", "#" + (data || user.character).color);
			}

			// Perform BBCode conversion
			$("#conversation div p").each(function(line) { user.meta.show_bbcode ? this.innerHTML = raw_bbencode(this.innerHTML, false) : $(this).html(bbremove(this.innerHTML)); });

			// Topbar and info panel
			if (chat.type == "group") {
				$("#topbar, #info_panel_link").click(function() {
					if (status != "chatting") { return false; }
					edit_info_panel.css("display") == "block" ? edit_info_panel.hide() : info_panel.toggle();
					return false;
				});
				// There are several places where we show the topic, so we use this to update them all.
				var topic = $(".topic");
				var info_panel = $("#info_panel");
				var description = $("#description");
				var rules = $("#rules");
				var info_panel_controls = $("#info_panel_controls");
				$("#edit_info_button").click(function() {
					info_panel.hide();
					// Only set these when we need them.
					$("#edit_info_description").val(chat.description);
					$("#edit_info_rules").val(chat.rules);
					edit_info_panel.show();
				});
				$(".set_topic_button").click(function() {
					var topic = prompt("Please enter a new topic for the chat:");
					if (topic != null) {
						$.post("/chat_api/set_topic", { "chat_id": chat.id, "topic": topic });
					}
				});
				var edit_info_panel = $("#edit_info_panel");
				$("#edit_info_form").submit(function() {
					var form_data = $(this).serializeArray();
					form_data.push({ name: "token", value: token });
					form_data.push({ name: "chat_id", value: chat.id });
					$.post("/chat_api/set_info", form_data);
					edit_info_panel.hide();
					return false;
				});
				$("#info_panel .close, #edit_info_panel .close").click(function() { info_panel.hide(); edit_info_panel.hide(); });
			}

			// PM chat list
			if (chat.type == "pm") {
				var pm_chat_list_container = $("#pm_chat_list_container");
				$("#pm_chat_list_container .close").click(function() { pm_chat_list_container.css("display", ""); });
				var pm_chat_list = $("#pm_chat_list");
				var pm_chat_list_template = Handlebars.compile($("#pm_chat_list_template").html());
				Handlebars.registerHelper("current_chat", function() {
					if ("url" in this) {
						return this.url == chat.url;
					} else if ("chat" in this) {
						return this.chat.url == chat.url;
					}
				});
				Handlebars.registerHelper("pm_username", function() { return this.chat.url.substr(3); });
				function refresh_pm_chat_list() {
					$.get("/chats/pm.json", {}, function(data) {
						pm_chat_list.html(pm_chat_list_template(data));
						var pm_chat_links = $("#pm_chat_list a").click(function() {
							// Hide PM chat list on mobile.
							if (pm_chat_list_container.css("display")) { pm_chat_list_container.css("display", ""); }
							var new_url = "pm" + this.href.substr(this.href.lastIndexOf("/"));
							if (chat.url == new_url) { return false; }
							next_chat_url = new_url;
							disconnect();
							pm_chat_links.removeClass("active");
							$(this).addClass("active");
							return false;
						});
					});
				}
			}

			// Sidebars
			var sidebars = $(".sidebar");
			var current_sidebar = null;
			function set_sidebar(sidebar_id) {
				sidebars.css("display", "none");
				if (
					!sidebar_id && status == "chatting"
					&& chat.type != "pm" && chat.type != "roulette"
					&& window.innerWidth >= 500
				) { sidebar_id = "user_list_container"; }
				if (sidebar_id) {
					$(body).addClass("with_sidebar");
					$("#" + sidebar_id).css("display", "block");
				} else {
					$(body).removeClass("with_sidebar");
				}
				current_sidebar = sidebar_id;
			}
			$(".sidebar .close").click(function() { set_sidebar(null); });

			// Mod tools
			if (chat.type == "group") {
				var mod_tools = $("#mod_tools");
				var flag_autosilence = $("#flag_autosilence").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "autosilence", "value": this.checked ? "on" : "off" });
				});
				var flag_publicity = $("#flag_publicity").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "publicity", "value": this.value });
				});
				var invites_link = $("#invites_link");
				var flag_style = $("#flag_style").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "style", "value": this.value });
				});
				var flag_level = $("#flag_level").change(function() {
					$.post("/chat_api/set_flag", { "chat_id": chat.id, "flag": "level", "value": this.value });
				});
				var flag_messages = $("#flag_messages");
				var flag_message_autosilence = $("#flag_message_autosilence");
				var flag_message_publicity = $("#flag_message_publicity");
				var flag_message_style = $("#flag_message_style");
				var flag_message_level = $("#flag_message_level");
			}

			// User list
			var user_list = $("#user_list");
			var user_list_template = Handlebars.compile($("#user_list_template").html());
			Handlebars.registerHelper("group_description", function(group) { return group_descriptions[group]; });
			Handlebars.registerHelper("is_you", function() { return this.meta.number == user.meta.number; });
			Handlebars.registerHelper("is_highlighted", function() { return user.meta.highlighted_numbers.indexOf(this.meta.number) != -1; });
			Handlebars.registerHelper("is_ignored", function() { return user.meta.ignored_numbers.indexOf(this.meta.number) != -1; });
			Handlebars.registerHelper("admin", function() { return user.meta.group == "admin"; });

			// Action list
			var action_user = null;
			var action_list = $("#action_list");
			var action_list_template = Handlebars.compile($("#action_list_template").html());
			var ranks = { "admin": Infinity, "creator": Infinity, "mod3": 3, "mod2": 2, "mod1": 1, "user": 0, "silent": -1 };
			function render_action_list() {
				var action_user_number = parseInt(this.id.substr(5));
				if (action_user && action_user_number == action_user.meta.number) {
					action_user = null;
					action_list.empty();
				} else {
					action_user = user_data[action_user_number];
					action_list.html(action_list_template(action_user));
					action_list.appendTo(this);
					$("#action_block").click(function() { block(action_user.meta.number); });
					$("#action_highlight").click(function() {
						if (user.meta.highlighted_numbers.indexOf(action_user.meta.number) != -1) {
							$(".unum_" + action_user.meta.number).removeClass("highlighted");
							user.meta.highlighted_numbers = user.meta.highlighted_numbers.filter(function(i) { return i != action_user.meta.number; })
						} else {
							$(".unum_" + action_user.meta.number).addClass("highlighted");
							user.meta.highlighted_numbers.push(action_user.meta.number);
						}
						$.post("/chat_api/save_variables", { "chat_id": chat.id, "highlighted_numbers": user.meta.highlighted_numbers.toString() });
					});
					$("#action_ignore").click(function() {
						if (user.meta.ignored_numbers.indexOf(action_user.meta.number) != -1) {
							$(".unum_" + action_user.meta.number).removeClass("ignored");
							user.meta.ignored_numbers = user.meta.ignored_numbers.filter(function(i) { return i != action_user.meta.number; })
						} else {
							$(".unum_" + action_user.meta.number).addClass("ignored");
							user.meta.ignored_numbers.push(action_user.meta.number);
						}
						$.post("/chat_api/save_variables", { "chat_id": chat.id, "ignored_numbers": user.meta.ignored_numbers.toString() });
					});
					$("#action_switch_character").click(function() { set_sidebar("switch_character"); });
					$("#action_settings").click(function() { set_sidebar("settings"); });
					$("#action_mod3, #action_mod2, #action_mod1, #action_user, #action_silent").click(function() {
						set_group(action_user.meta.number, this.id.substr(7));
					});
					$("#action_kick, #action_ban").click(function() {
						if (this.id == "action_ban") {
							var reason = prompt("Please provide a reason for this ban.");
							if (reason == null) { return; }
						}
						user_action(action_user.meta.number, this.id.substr(7), reason || "");
					});
					$("#action_request_username").click(function() {
						$.post("/chat_api/request_username", { "chat_id": chat.id, "number": action_user.meta.number });
					});
					$("#action_look_up_user").click(function() {
						$.post("/chat_api/look_up_user", { "chat_id": chat.id, "number": action_user.meta.number });
					});
				}
			}
			Handlebars.registerHelper("can_block", function(new_group) { return can_block(this.meta.number); });
			Handlebars.registerHelper("can_set_group", function(new_group) { return can_set_group(new_group, this.meta.group); });
			Handlebars.registerHelper("can_perform_action", function(action) { return can_perform_action(action, this.meta.group); });
			Handlebars.registerHelper("set_user_text", function() { return this.meta.group == "silent" ? "Unsilence" : "Unmod"; });

			// Switch character
			var switch_character = $("#switch_character");
			$("select[name=character_id]").change(function() {
				if (this.value != "") {
					$.get("/characters/"+this.value+".json", {}, update_character);
				}
			});
			initialize_character_form();
			$("#switch_character_form").submit(function() {
				if ($("input[name=name]").val().trim() == "") {
					alert("You can't chat with a blank name!");
				} else if ($("input[name=color]").val().match(/^#?[0-9a-fA-F]{6}$/) == null) {
					alert("You entered an invalid hex code.");
				} else {
					var form_data = $(this).serializeArray();
					form_data.push({ name: "token", value: token });
					form_data.push({ name: "chat_id", value: chat.id });
					$.post("/chat_api/save", form_data, function(data) {
						user = data;
						set_temporary_character(null);
					});
				}
				set_sidebar(null);
				return false;
			});

			// Settings
			var settings = $("#settings");
			$(".variable").click(function() {
				var data = { "chat_id": chat.id };
				data[this.id] = this.checked ? "on" : "off";
				$.post("/chat_api/save_variables", data);
				user.meta[this.id] = this.checked;
				if (this.id == "desktop_notifications" && this.checked && "Notification" in window && Notification.permission != "granted") {
					init_notifications();
				} else if (this.id == "typing_notifications") {
					if (chat.type == "pm" || chat.type == "roulette") {
						if (previous_status_message) {
							status_bar.text(previous_status_message);
							previous_status_message = null;
						}
					} else {
						status_bar.text(messages_method == "websocket" && this.checked ? " " : "");
					}
				}
				parse_variables();
			});
			$("#desktop_notifications").prop("disabled", !("Notification" in window));
			function parse_variables() {
				user.meta.show_preview ? text_preview.show() : text_preview.hide();
				user.meta.show_system_messages ? conversation.removeClass("hide_system_messages") : conversation.addClass("hide_system_messages");
				resize_conversation();
			}
			$("#subscribed").click(function() {
				$.post("/" + chat.url + "/" + (this.checked ? "subscribe" : "unsubscribe"));
				user.meta.subscribed = this.checked;
			});
			$("#theme_form").submit(function() {
				var form_data = $(this).serializeArray();
				var new_theme = $(this).find("select").val();
				form_data.push({ name: "chat_id", value: chat.id });
				$.post(this.action, form_data, function() {
					var theme_stylesheet = $("#theme_stylesheet");
					if (new_theme) {
						var stylesheet_url = "/static/css/themes/" + new_theme + ".css";
						update_theme(new_theme);
						if (theme_stylesheet.length == 1) {
							theme_stylesheet.attr("href", stylesheet_url);
						} else {
							$("<link>").attr({id: "theme_stylesheet", rel: "stylesheet", href: stylesheet_url}).appendTo(document.head);
						}
					} else {
						theme_stylesheet.remove();
					}
				});
				return false;
			});

			// Conversation
			function is_at_bottom() {
				var current_scroll = conversation.scrollTop() + conversation.height();
				var max_scroll = conversation[0].scrollHeight;
				return max_scroll - current_scroll < 30;
			}
			function scroll_to_bottom() { conversation.scrollTop(conversation[0].scrollHeight); }
			function resize_conversation() {
				var scroll_after_resize = is_at_bottom();
				conversation.css("bottom", send_form.height() + 10 + "px");
				if (scroll_after_resize) { scroll_to_bottom(); }
			}
			var status_bar = $("#status_bar");
			var previous_status_message;

			// Send form
			var typing;
			var typing_timeout;
			var text_preview = $("#text_preview");
			function set_text_preview(text) {
				text_preview.html(bbencode(text));
				resize_conversation();
			}

			var changed_since_draft = false;
			window.setInterval(function() {
				if (changed_since_draft) {
					console.log("changed");
					$.post("/chat_api/draft", { "chat_id": chat.id, "text": text_input.val().trim() });
				}
				changed_since_draft = false;
			}, 15000);

			var text_input = $("input[name=text]").keydown(function() {
				changed_since_draft = true;
				if (messages_method == "websocket") {
					window.clearTimeout(typing_timeout);
					if (!typing) {
						typing = true;
						ws.send("typing");
					}
					typing_timeout = window.setTimeout(function() {
						typing = false;
						ws.send("stopped_typing");
					}, 1000);
				}
			}).keyup(function() {
				if (user.meta.show_preview) {
					text = this.value.trim()
					if (text[0] == "/") {
						var text = text.substr(1);
						var command_description = get_command_description(text);
						// Look up a saved character.
						if (!command_description) {
							// Skip all this if it's the same character as last time.
							if (temporary_character && text.lastIndexOf(temporary_character.shortcut + " ", 0) == 0) {
								set_text_preview(apply_quirks(text.substr(temporary_character.shortcut.length + 1)));
								return;
							}
							for (var shortcut in character_shortcuts) {
								if (text.lastIndexOf(shortcut + " ", 0) == 0) {
									$.get("/characters/" + character_shortcuts[shortcut] + ".json", {}, function(data) {
										set_temporary_character(data);
										set_text_preview(apply_quirks(text.substr(shortcut.length + 1)));
									}).error(function() {
										set_temporary_character(null);
										delete character_shortcuts[shortcut];
										text_input.keyup();
									});
									return;
								}
							}
						}
						set_text_preview(command_description || text);
					} else if (text.substr(0, 7) == "http://" || text.substr(0, 8) == "https://" || ["((", "[[", "{{"].indexOf(text.substr(0, 2)) != -1) {
						set_text_preview(text);
					} else {
						set_text_preview(apply_quirks(text));
					}
					// Clear the temporary character if necessary.
					if (temporary_character) { set_temporary_character(null); }
				}
			});
			var send_form = $("#send_form").submit(function() {
				var data = { "chat_id": chat.id, "text": text_input.val().trim(), "type": "ic" };
				if (data.text == "") { return false; }
				if (data.text[0] == "/") {
					data.text = data.text.substr(1);
					// Try to parse the text as a command, and skip the rest if we can.
					var executed = execute_command(data.text);
					if (executed) {
						text_input.val("");
						if (messages_method == "websocket") { typing = false; ws.send("stopped_typing"); }
						return false;
					}
					// If the current temporary character matches, apply their quirks.
					if (temporary_character && data.text.lastIndexOf(temporary_character.shortcut + " ", 0) == 0) {
						data.text = apply_quirks(data.text.substr(temporary_character.shortcut.length + 1)).trim();
						data.character_id = temporary_character.id;
					} else {
						// If not, look up another saved character.
						for (var shortcut in character_shortcuts) {
							if (data.text.lastIndexOf(shortcut + " ", 0) == 0) {
								$.get("/characters/" + character_shortcuts[shortcut] + ".json", {}, function(data) {
									set_temporary_character(data);
									send_form.submit();
								}).error(function() {
									set_temporary_character(null);
									delete character_shortcuts[shortcut];
									send_form.submit();
								});
								return false;
							}
						}
						// If that doesn't work, make sure the temporary character is cleared.
						if (temporary_character) { set_temporary_character(null); }
					}
				} else if (data.text.substr(0, 7) == "http://" || data.text.substr(0, 8) == "https://") {
					// Don't apply quirks if the message starts with a link.
				} else if (["((", "[[", "{{"].indexOf(data.text.substr(0, 2)) != -1) {
					// Don't apply quirks to OOC messages
					data.type = "ooc";
				} else {
					data.text = apply_quirks(data.text).trim();
				}
				// Check if it's blank before and after because quirks may make it blank.
				if (data.text == "") { return false; }
				$.post("/chat_api/send", data);
				text_input.val("");
				last_alternating_line = !last_alternating_line;
				if (temporary_character) { set_temporary_character(null); }
				changed_since_draft = false;
				typing = false;
				return false;
			});
			var send_button = send_form.find("button[type=submit]");

			// Typing quirks
			var last_alternating_line = false;
			function apply_quirks(text) {
				var character = (temporary_character || user.character);
				// Case options.
				// ["case"] instead of .case because .case breaks some phones and stuff.
				switch (character["case"]) {
					case "lower":
						// Adaptive lower
						// Part 1: convert words to lower case if they have at least one lower case letter in them.
						text = text.replace(/\w*[a-z]+\w*/g, function(str) { return str.toLowerCase(); });
						// Part 2: convert lone capital letters (eg. I) to lower case.
						// Find single capital letters with adjacent lower case ones, potentially looping in case they overlap.
						text = text.replace(/(^|[a-z])(\W*[A-Z]\W*([a-z]|$))+/g, function(str) { return str.toLowerCase(); });
						break;
					case "upper":
						text = text.toUpperCase();
						break;
					case "title":
						// Capitalise the first letter at the beginning, and after a word break if it's not a hyphen or an apostrophe.
						text = text.toLowerCase().replace(/(^|[^'-]\b)\w/g, function(str) { return str.toUpperCase(); });
						break;
					case "inverted":
						// Lower case the first letter at the beginning, the first letter of each sentence, and lone Is.
						text = text.toUpperCase().replace(/^.|[,.?!]\s+\w|\bI\b/g, function(str){ return str.toLowerCase(); });
						break;
					case "alternating":
						// Pick up pairs of letters (optionally with whitespace in between) and capitalise the first in each pair.
						text = text.toLowerCase().replace(/(\w)\W*\w?/g, function(str, p1){ return str.replace(p1, p1.toUpperCase()); });
						break;
					case "alt-lines":
						text = last_alternating_line ? text.toUpperCase() : text.toLowerCase();
						break;
					case "proper":
						// Capitalise the first letter at the beginning, the first letter of each sentence, and lone Is.
						text = text.replace(/^.|[.?!]\s+\w|\bi\b/g, function(str) { return str.toUpperCase() });
						break;
					case "first-letter":
						// Part 1: same as adaptive lower.
						text = text.replace(/\w*[a-z]+\w*/g, function(str) { return str.toLowerCase(); });
						text = text.replace(/(^|[a-z])(\W*[A-Z]\W*([a-z]|$))+/g, function(str) { return str.toLowerCase(); });
						// Part 2: capitalise the first letter at the beginning and the first letter of each sentence.
						text = text.replace(/^.|[.?!]\s+\w/g, function(str) { return str.toUpperCase() });
						break;
				}
				// Ordinary replacements. Escape any regex control characters before replacing.
				character.replacements.forEach(function(replacement) {
					RegExp.quote = function(str) {return str.replace(/([.?*+^$[\]\\(){}|-])/g, "\\$1"); }
					var re = new RegExp(RegExp.quote(replacement[0]), "g");
					text = text.replace(re, replacement[1]);
				});
				// Regex replacements
				character.regexes.forEach(function(replacement) {
					try {
						re = new RegExp(replacement[0], "g");
						text = text.replace(re, replacement[1]);
					} catch (e) {
						text = "Regex parsing error :(";
						return;
					}
				});
				// Prefix and suffix
				return character.quirk_prefix + text + character.quirk_suffix;
			}

			// Abscond/reconnect button
			var abscond_button = $("#abscond_button").click(function() {
				if (status == "chatting") {
					if (confirm("Are you sure you want to abscond?")) { disconnect(); }
				} else if (chat.type == "searched") {
					location.href = "/search";
				} else if (chat.type == "roulette") {
					location.href = "/roulette";
				} else {
					connect();
				}
			});

			// Other buttons
			$("#user_list_button").click(function() {
				chat.type == "pm" ? $("#pm_chat_list_container").show() : set_sidebar("user_list_container");
			});
			$("#switch_character_button").click(function() { set_sidebar(current_sidebar != "switch_character" ? "switch_character" : null); });
			$("#settings_button").click(function() { set_sidebar(current_sidebar != "settings" ? "settings" : null); });

			// Global announcements
			var announcement_template = Handlebars.compile($("#announce_template").html());

			function announcement_banner(title, text) {
				$("#global_announcements").append(announcement_template({
					announce: {
						title: title,
						text: text
					}
				}));
				setTimeout(function(){ $(".announcement").addClass("show"); }, 100);
			}

			body.on("click", ".announcement", function() {
				var announcement = $(this);

				announcement.removeClass("show");
				setTimeout(function() {
					announcement.remove();
				}, 1000)
			});

			// Theme specific code
			function update_theme(theme) {
				$(".sidebar").removeClass("omg kringle manorah geromy");
				$(".sbigman").remove();

				if (typeof theme === "string" && theme.match(/gristmas/)) {
					if (theme.match(/noanimate/)) {
						$('body').addClass('stopmoving');
					} else {
						$('body').removeClass('stopmoving');
					}

					userAgent = window.navigator.userAgent;
					if(/iP(hone|od|ad)/.test(userAgent) == false) {
						$( "body" ).append( '<div class="sbigman"></div>' );
					}

					if(/Android/i.test(userAgent) || /iP(hone|od|ad)/.test(userAgent)) {
						$( "body" ).addClass("nodrift");
					}

					// randomised sidebar in here 8ecause them's the 8r8ks
					var rnjesus = Math.floor((Math.random() * 100) + 1);
					if (rnjesus < 2) {
						$('.sidebar').addClass("omg");
					} else if (rnjesus < 46) {
						$('.sidebar').addClass("kringle");
					} else if (rnjesus < 90) {
						$('.sidebar').addClass("manorah");
					} else {
						$('.sidebar').addClass("geromy");
					}
				}
			}

			// Run theme specific code.
			update_theme($("#theme_form select").val());

			// Initalize push if notifications are enabled.
			if (user.meta.desktop_notifications && typeof Notification != "undefined") {
				init_push();
			}

			// Now all that's done, let's connect
			connect();

		},
		"log": function(show_bbcode) {
			// Perform BBCode conversion
			$("#archive_conversation div p").each(function(line) { show_bbcode ? this.innerHTML = raw_bbencode(this.innerHTML, false) : $(this).html(bbremove(this.innerHTML)); });
		},
		// Broadcast page
		"broadcast": function() {
			$("input[name=title]").keyup(function() {
				$(".announcement h2").text(this.value);
			});

			$("textarea[name=text]").keyup(function() {
				$(".announcement p").text(this.value || "[no message]");
			});

			$("input[name=headercolor]").change(function() {
				$(".announcement").css("background-color", this.value);
			});
		},
	};
})();
