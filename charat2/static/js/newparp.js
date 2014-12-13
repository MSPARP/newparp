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

			// Long polling
			function launch_long_poll() {
				$.post("/chat_api/messages", { "chat_id": chat.id, "after": latest_message}, receive_messages).complete(function(jqxhr, text_status) {
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

			// Parsing and rendering messages
			function receive_messages(data) {
				if (typeof data.messages != "undefined" && data.messages.length != 0) { data.messages.forEach(render_message); }
			}

			function render_message(message) {
				latest_message = message.id;
				var p = $("<p>").attr("id", "message_"+message.id).addClass("message_"+message.type+" user_"+message.user.id);
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

			// Now all that's done, let's connect
			var status = "chatting";
			launch_long_poll();
			conversation.scrollTop(conversation[0].scrollHeight);

		},
	};
})();
