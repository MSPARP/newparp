var msparp = (function() {
	return {
		"home": function() {
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
