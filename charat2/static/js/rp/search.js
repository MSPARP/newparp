var search = (function() {

	var characterSelect = $("#characterSelect");
	var characterTags = $("#characterTags");
	var searchButton = $("#searchButton").click(startSearch);

	var searching = false;

	function startSearch() {
		if (!searching) {
			searching = true;
			searchRequest();
			$(document.body).addClass("searching");
		}
	}

	function stopSearch() {
		searching = false;
		$.ajax("/search/stop", { "type": "POST", data: {}, "async": false });
		$(document.body).removeClass("searching");
	}

	function searchRequest() {
		$.post("/search", {
            "character_id": characterSelect.val(),
            "tags": characterTags.val(),
        }, function(data) {
			console.log(data);
			if (data.status == "matched") {
				searching = false;
				window.location.href = "/" + data.url;
			} else if (data.status == "quit") {
				searching = false;
			}
		}).complete(function() {
			if (searching) {
				searchRequest();
			}
		});
	}

	$(window).unload(function () {
		if (searching) {
			stopSearch();
		}
	});

	return {
		"startSearch": startSearch,
		"stopSearch": stopSearch,
	};

})();

