# Professorlocke
Pokemon Informational Quiz (base quiz)! What is the Professorlocke? I wanted to spice up my challenge of a nuzlocke in Pokemon, and improve my knowledge of a franchise I love. So I wanted to make a quiz I could take and stream.

This is that quiz. It pulls from PokéApi.co for Pokémon and species data, plays a victory tune, displays a sprite, and holds you to your standard.

**Link to project:** https://github.com/FabledTyromancer/Professorlocke

# How It's Made:

Language: Python, a lot of standard dependencies, but some non-standard: winsound for the victory sounds, pillow for the images. You can remove them in the code if you want.

It's a bit of a quirky thing, mainly parsing jsons and wrapping it up pretty for the dopamine receptors, but it's fairly moldable. A lot of data is passed between the packages, so it should be fairly manageable to make any modifications you like without breaking it entirely, just make sure you update it across the requisite packages.

# How to Use:

For the initial install, again, make sure you have the dependencies above. On Windows, you're probably looking at C:\Users\[your user here]. There will be a lengthy download when you launch it for the first time, with an initialization displayed in the GUI and some text printed in the terminal, but there are areas where you can activate/reactivate debug lines if you have problems. If you want to add sounds, be sure you put them in the cache file (professor_cache) created on the os.path. I have added a full zipped version of the cache that you can download and unzip in the right spot, to not pull from the API, but I anticipate it will get out of date fast.

It's also not the nicest on the API to do that much pulling, so please be mindful! But if you want to add more parameters to pull from the species or pokemon files, you can do so in the jsongenerator package, if you want to add more questions, do so in the quiz_logic package, just make sure you're consistent. The UI and Professorlocke shouldn't care one way or the other.

# See it in action:

If you want to see the work in action, please check me out on twitch.tv/fabledtyromancer or youtube.com/@FabledTyromancer. Or, if you just want to support me, those are the best ways.

# What now? / Contact

You are free to modify this code, fork it, etc, just provide some credit to me for the idea, share this repository, and have fun. I'm ass at coding, this was literally my first project (and used some LLM assistance... hence any really weird crap), so if you have suggestions for revisions, ways to improve it, or just want to see me do something, reach out to me at fabledtyromancer@gmail.com.

# Thanks

My eternal thanks to the wonderful Chlotendo for her help and patience!
Also, y'know, the people who run a free API of Pokémon data. PokeAPI folks, thank you for this incredible resource!
