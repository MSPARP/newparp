var msparp = (function() {

	// Character info
	function update_character(data) {
		if (typeof data["search_character"]!= "undefined") {
			$("select[name=search_character_id]").val(data["search_character"]["id"]);
		}
		$("#toggle_with_settings").prop("checked", true);
		$("input[name=name]").val(data["name"]);
		$("input[name=alias]").val(data["alias"]).keyup();
		$("input[name=color]").val("#"+data["color"]).change();
		if (typeof data["text_preview"]!= "undefined") {
			$("#text_preview").text(data["text_preview"]);
		} else if (typeof data["search_character"]!= "undefined") {
			$("#text_preview").text(data["search_character"]["text_preview"]);
		}
		if (data["quirk_prefix"] != "" || data["quirk_suffix"] != "" || data["case"] != "normal" || data["replacements"].length != 0 || data["regexes"].length != 0) {
			$("#toggle_typing_quirks").prop("checked", true);
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
		$(this.parentNode).remove();
		return false;
	}
	function add_replacement(e, from, to) {
		new_item = $("<li><input type=\"text\" name=\"quirk_from\" size=\"10\"> to <input type=\"text\" name=\"quirk_to\" size=\"10\"> <button type=\"button\" class=\"delete_replacement\">x</button></li>");
		if (from && to) {
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

	// Regex list
	function delete_regex(e) {
		$(this.parentNode).remove();
		return false;
	}
	function add_regex(e, from, to) {
		new_item = $("<li><input type=\"text\" name=\"regex_from\" size=\"10\"> to <input type=\"text\" name=\"regex_to\" size=\"10\"> <button type=\"button\" class=\"delete_regex\">x</button></li>");
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

	return {
		// Homepage
		"home": function() {

			// Saved character dropdown
			$("select[name=character_id]").change(function() {
				if (this.value != "") {
					$.get("/characters/"+this.value+".json", {}, update_character);
				}
			});

			// Search character dropdown
			$("select[name=search_character_id]").change(function() {
				$.get("/search_characters/"+this.value+".json", {}, update_character);
			});

			// Text preview
			var text_preview_container = $("#text_preview_container");
			var text_preview_alias = $("#text_preview_alias");
			$("input[name=alias]").keyup(function() {
				if (this.value == "") {
					text_preview_alias.text("");
				} else {
					text_preview_alias.text(this.value + ": ");
				}
			});
			$("input[name=color]").change(function() {
				text_preview_container.css("color", this.value);
			});

			// Replacement list
			$('.delete_replacement').click(delete_replacement);
			$('#add_replacement').click(add_replacement);
			$('#clear_replacements').click(clear_replacements);

			// Regex list
			$('.delete_regex').click(delete_regex);
			$('#add_regex').click(add_regex);
			$('#clear_regexes').click(clear_regexes);

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
		"search": function() {

			var searching = false;
			var searcher_id;

			function start_search() {
				if (!searching) {
					searching = true;
					$(document.body).addClass("searching");
					$.post("/search", {}, function(data) {
						searcher_id = data.id;
						continue_search();
					}).error(function() {
						searching = false;
						$(document.body).removeClass("searching").addClass("search_error");
					});
				}
			}

			function continue_search() {
				if (searching) {
					$.post("/search/continue", { "id": searcher_id }, function(data) {
						console.log(data);
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
				$.ajax("/search/stop", { "type": "POST", data: { "id": searcher_id }, "async": false });
				$(document.body).removeClass("searching");
			}

			$(window).unload(function () {
				if (searching) {
					stop_search();
				}
			});

			start_search();

		},
		// Chat window
		"chat": function(chat, user, latest_message) {

			console.log(chat);
			console.log(user);
			console.log(latest_message);

			var conversation = $("#conversation");
			var status;
			var user_data = {};

			// Long polling
			function launch_long_poll() {
				$.post("/chat_api/messages", { "chat_id": chat.id, "after": latest_message }, receive_messages).complete(function(jqxhr, text_status) {
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
					$.post("/chat_api/ping", { "chat_id": chat.id }).complete(function() { window.setTimeout(ping, 10000); });
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
					$.ajax("/chat_api/quit", { "type": "POST", data: { "chat_id": chat.id }, "async": false});
				}
			});

			// Parsing and rendering messages
			function receive_messages(data) {
				if (typeof data.messages != "undefined" && data.messages.length != 0) { data.messages.forEach(render_message); }
				if (typeof data.users != "undefined") {
					user_list.html(user_list_template(data));
					user_list.find("li").click(render_action_list);
					// Store user data so we can look it up for action lists.
					for (var i = 0; i < data.users.length; i++) {
						user_data[data.users[i].meta.user_id] = data.users[i];
					}
				}
			}
			function render_message(message) {
				latest_message = message.id;
				var p = $("<p>").attr("id", "message_" + message.id);
				p.addClass("message_" + message.type + " user_" + message.user.id);
				p.css("color", "#" + message.color);
				if (message.type == "me") {
					p.text("* " + message.name + " " + message.text);
				} else if (message.alias != "") {
					p.text(message.alias + ": " + message.text);
				} else {
					p.text(message.text);
				}
				p.appendTo(conversation);
				conversation.scrollTop(conversation[0].scrollHeight);
			}

			// Sidebars
			$(".close").click(function() { $(this.parentNode).hide(); });

			// User list
			var user_list = $("#user_list");
			var user_list_template = Handlebars.compile($("#user_list_template").html());
			Handlebars.registerHelper("group_description", function(group) {
				return {
					"admin": "God tier moderator - MSPARP staff.",
					"creator": "Chat creator - can silence, kick and ban other users.",
					"mod": "Professional Wet Blanket - can silence, kick and ban other users.",
					"mod2": "Bum's Rusher - can silence and kick other users.",
					"mod3": "Amateur Gavel-Slinger - can silence other users.",
					"user": "",
					"silent": "Silenced.",
				}[group];
			});
			Handlebars.registerHelper("is_you", function() { return this.meta.user_id == user.meta.user_id; });

			// Action list
			var action_user;
			var action_list = $("#action_list");
			var action_list_template = Handlebars.compile($("#action_list_template").html());
			var ranks = { "admin": Infinity, "creator": Infinity, "mod": 4, "mod2": 3, "mod3": 2, "user": 1, "silent": 0 };
			function render_action_list() {
				action_user = user_data[parseInt(this.id.substr(5))];
				action_list.html(action_list_template(action_user));
				$("#action_mod, #action_mod2, #action_mod3, #action_user, #action_silent").click(set_group);
				action_list.find("li").click(function() { action_list.empty(); action_user = null; });
			}
			Handlebars.registerHelper("can_set_group", function(new_group, action_user) {
				console.log(new_group);
				// Don't bother if they're already this group.
				if (ranks[new_group] == ranks[this.meta.group]) { return false; }
				// You can't set groups at all if you're not a mod.
				if (ranks[user.meta.group] < 2) { return false; }
				// You can only set the group to one which is below yours.
				if (ranks[new_group] >= ranks[user.meta.group]) { return false; }
				// You can only set the group of people whose group is below yours.
				if (ranks[this.meta.group] >= ranks[user.meta.group]) { return false; }
				return true;
			});
			Handlebars.registerHelper("set_user_text", function() {
				if (this.meta.group == "silent") { return "Unsilence"; }
				return "Unmod";
			});
			function set_group() {
				$.post("/chat_api/set_group", { "chat_id": chat.id, "user_id": action_user.meta.user_id, "group": this.id.substr(7) });
			}

			// Send form
			var text_input = $("input[name=text]");
			var send_form = $("#send_form").submit(function() {
				var message_text = text_input.val().trim();
				if (message_text == "") { return false; }
				$.post("/chat_api/send", { "chat_id": chat.id, "text": message_text });
				text_input.val("");
				return false;
			});
			conversation.css("bottom", send_form.height() + 10 + "px");

			// Abscond/reconnect button
			var abscond_button = $("#abscond_button").click(function() {
				if (status == "chatting") {
					if (confirm("Are you sure you want to abscond?")) { disconnect(); }
				} else {
					// XXX make this search again in searched chats.
					connect();
				}
			});

			// Other buttons
			$("#chat_info_button").click(function() { $("#chat_info").show(); });

			// Connecting and disconnecting
			function connect() {
				status = "chatting";
				launch_long_poll();
				window.setTimeout(ping, 10000);
				$(document.body).addClass("chatting");
				conversation.scrollTop(conversation[0].scrollHeight);
				abscond_button.text("Abscond");
			}
			function disconnect() {
				status = "disconnected";
				$.ajax("/chat_api/quit", { "type": "POST", data: { "chat_id": chat.id }, "async": false});
				$(document.body).removeClass("chatting");
				abscond_button.text("Join");
			}

			// Now all that's done, let's connect
			connect();

		},
	};
})();
