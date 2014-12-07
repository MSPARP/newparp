var msparp = (function() {

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
		"home": function() {
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
	};
})();
