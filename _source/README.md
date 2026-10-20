# Trinity Care Continuum website: how to edit it

The live site is made of plain files in the repo root. Most of them are **generated**
from the files in this `_source/` folder, so make your edits here.

## To change something

1. Edit the page or file you want (see "Where things live" below).
2. From the repo root, run:

       python3 _source/build.py

   It rebuilds every page, the sitemap and robots.txt, and checks every internal
   link and #anchor. It prints something like
   `Built 11 pages. Checked 364 internal links: 0 problem(s).`
   If it reports a problem, fix that before you publish.
3. Commit and push:

       git add -A
       git commit -m "Describe your change"
       git push

   GitHub Pages publishes it in a minute or two.

Only Python 3 is needed. There is nothing to install.

## Where things live

| To change...                                   | Edit this                                   |
| ---------------------------------------------- | ------------------------------------------- |
| Phone, email, fax, referral form link          | the `SITE` block at the top of `build.py`   |
| Text on a page                                 | `_source/pages/<page>.html`                 |
| Page title / description (search results)      | the header lines at the top of that page    |
| Menu items and the Programs dropdown           | `header_html` and `PROGRAM_NAV` in `build.py` |
| Footer                                         | `FOOTER` in `build.py`                      |
| Top bar ("Telehealth across all of Texas")     | `TOPLINE` in `build.py`                     |
| The "A clear path forward" 4 steps             | `_source/partials/steps.html`               |
| The Texas map and metro list                   | `_source/partials/map.html`                 |
| The big call-to-action band at the page bottom | `_source/partials/cta.html`                 |
| Colors, fonts, spacing                         | `_source/assets/styles.css`                 |

Do **not** edit `index.html`, the folders like `palliative-care/`, `styles.css`,
`sitemap.xml` or `robots.txt` in the repo root. They get overwritten when you rebuild.

## Placeholders

Inside page files you can use these and they are filled in automatically:
`{{PHONE}}`, `{{PHONE_TEL}}`, `{{EMAIL}}`, `{{FAX}}`, `{{FAX_TEL}}`, `{{JOTFORM}}`,
and the blocks `{{STEPS}}`, `{{MAP}}`, `{{CTA}}`.

## Adding a page

1. Copy an existing file in `_source/pages/` (for example `faq.html`) to a new name.
2. Change the header lines at the top (path, title, description, headline, etc.).
   The line `---` ends the header; everything after it is the page body.
3. Run the build. The new page is added to the sitemap automatically.
4. Link to it from somewhere (the menu, footer, or another page).

## Notes

* All links are written from the site root (like `/faq/`), which works because the site
  uses its own domain. If you open a built page straight from your disk it will look
  unstyled. To preview locally, run `python3 -m http.server 8000` in the repo root and
  visit http://localhost:8000
* Pages must not use analytics, ad pixels, embeds or forms without checking privacy and
  HIPAA implications first. The Privacy Notice says the site uses none.
* Page text is drafted for review. Have your compliance contact approve clinical,
  coverage and eligibility wording before changing it.
