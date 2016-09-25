jQuery(function($) {
	$('.go-next-icon').click(function(){
	    var nextSection = $(this).closest('section').next('section');

	    $('html, body').animate({
	        scrollTop: nextSection.offset().top
	    }, 500);
	});
	$('body').on('submit', '#searchSong', function(e) {
		songSearch(); // Trigger on submit form
		e.preventDefault(); // Stop form from submitting
	});
	$( "#songSearchInput").on('input',function() {
	  	songSearch(); // Trigger on writing in input
	});
	var waitingSongSearch = false; // Setup waiting parameter

	function songSearch() {
		// Check if search should be conducted (or else wait for timeout)
		if (!waitingSongSearch) {
			var output = '';
			$('#searchResult').empty(); // clear the searchresult field
			var keyword = $('#songSearchInput').val(); // get the keyword to search for
			if (keyword.length >= 3) { // check if keyword length is longer than or equal to 3

				// AJAX call to search song api endpoint
				$.ajax({
		      		type: 'GET',
		      		dataType: "json",
		      		url: '/search/song/JSON?s=' + keyword,
		      		success: function(result) {
		      			if (result.Songs.length == 0) {
		      				// check if Songs in result exist
		      				output = '<p>No Result</p>';
		      			} else {
		      				$(result.Songs).each(function( index ) {
		      					// IF they exist loop through them and add them to the output
		      					var song = result.Songs[index];
		      					output += '<p class="song-result" data-song-id="' + song.id +'">' + song.title + ' - ' + song.artist + ' <span>+</span></p>';
							});
		      			}
		      			// Append a create song link at the end of output always
		      			output += "<p><small class='text-muted'>Can't find the right song? <a href='/song/create'>Create one instead!</a></small></p>"
		      			$('#searchResult').append(output); // append the output to the searchResult div
		      		}
		      	})
			}
	      	waitingSongSearch = setTimeout(function() {
	      		waitingSongSearch = false;
	      		// set a 250 ms timeout to wait for before calling the api endpoint again
	      	}, 250);
		}
	}
	$('body').on('click', '.song-result', function() {
		// WHen clicking on a result from search
		var songID = $(this).attr('data-song-id'); //fetch the songid
		var playlistID = $('meta[name=playlist_id]').attr("content"); // fetch the playlistid
		// Ajax call to connect song to playlist api endpoint
		$.ajax({
      		type: 'GET',
      		dataType: "json",
      		url: '/playlists/' + playlistID + '/song/' + songID + '/add',
      		success: function(result) {
      			if (result.success) {
      				// Return a notification if song is added
      				$('.message-alert-box').append('<div class="alert alert-info alert-dismissible fade in" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>Song added to playlist</div>');
      				// ToDo add the song to the list (I really should use react instead or something for this)
      			} else {
      				// If failed add a notification also output the errors in the console.
      				$('.message-alert-box').append('<div class="alert alert-info alert-dismissible fade in" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>Song has already been added to playlist</div>');
      				console.log(result.error);
      			}
      		}
      	})
	});
	$('body').on('click', '.remove-song', function() {
		// When clicking to remove a song from a playlist (doesn't delete the song just disconnect the pairing)
		var confirmRemove = confirm("Are you sure you want to remove this song?"); // ask for confirmation for those who are fat fingered
		playlistSongID = $(this).attr('data-ID'); // fetch the playlistsongid which is a compilation of the playlist_id and song_id
		if (confirmRemove) {
			// if confirm to remove do ajax call to delete playlist-song connection api endpoint
			$.ajax({
	      		type: 'GET',
	      		dataType: "json",
	      		url: '/playlistsongs/delete/' + playlistSongID,
	      		success: function(result) {
	      			if (result.success) {
	      				$('.single-song-list-' + playlistSongID).remove(); // remove the song from the playlist
	      				// Notify that remove is completed
	      				$('.message-alert-box').append('<div class="alert alert-info alert-dismissible fade in" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>Song removed from playlist</div>');
	      			} else {
	      				// If fail fail silently and just log it in the console
	      				console.log(result.error);
	      			}
	      		}
	      	})
		}
	});

});