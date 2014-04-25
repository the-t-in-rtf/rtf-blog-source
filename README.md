rtf-blog-source
===============

The pelican source for my RtF blog slash web site, [http://the-t-in-rtf.github.io/].

To create a new blog post:

1. Add any new blog posts to the content directory, making sure to include the required metadata at the top of the file.
2. Add any images to the images directory.

To deploy an update to the site:

1. Check out the "output" repository in the same parent directory as this repo.
2. Confirm that the output directory name matches the location in pelicanconf.py
3. Run the "pelican" command.
4. Change to the output directory
5. Run commands like the following:
    * `git add`
    * `git commit -m "I'm not a total tool and know how to leave comments"`
    * `git push`
6. Open [the site](http://the-t-in-rtf.github.io/) and review for broken links, images, and general polish.
