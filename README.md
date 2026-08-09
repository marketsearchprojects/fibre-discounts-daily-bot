# FibreDiscounts Daily Bot

Source code for a narrowly scoped educational posting bot proposed for
[`r/FibreDiscounts`](https://www.reddit.com/r/FibreDiscounts/), operating as
[`u/FrierenInsights`](https://www.reddit.com/user/FrierenInsights/).

## Status

**Not authorised and not publishing.** The scheduled workflow has a hard gate:
the repository variable `REDDIT_APPROVAL_GRANTED` must be exactly `true`. It
must remain false until Reddit gives explicit API approval, including written
approval for the disclosed commercial referral use.

## What it does

On each eligible run the bot:

1. reads a small allowlist of external UK broadband RSS feeds;
2. selects a recent, previously unused fibre-related item;
3. sends only that external feed item to OpenAI for a concise factual summary;
4. validates the draft against local editorial rules;
5. checks the newest posts in `r/FibreDiscounts` solely for duplicate-source
   prevention;
6. resolves one of three existing post flairs; and
7. submits at most one self-post, then records its source URL and Reddit post ID.

The three allowed flairs are:

- `UK Fibre News`
- `Technology Explainer`
- `Market Development`

Each title begins `Ad |` because the post contains a rewarded referral code;
this is a disclosure label, not an additional flair. Each post is limited to
two paragraphs. Paragraph one is the source-linked educational update.
Paragraph two is a plainly labelled referral message:

> Ad — If YouFibre is available at your address and suits your needs, enter
> referral code `KFJY3B` during checkout to claim any currently eligible
> switching reward. I may also receive a referral reward. Check YouFibre's
> current terms before ordering or cancelling an existing service.

The application rejects unsupported superiority claims, guarantees, referral
reward amounts, and more than two paragraphs. It does not vote, comment,
message users, cross-post, scrape Reddit, profile users, or send Reddit content
to an AI model. Its expected Reddit traffic is five API requests on a posting
day: OAuth, identity verification, recent-post duplicate check, flair lookup,
and submission.

## Why this is not Devvit

Devvit supports scheduled jobs, but an unattended Devvit scheduler publishes
through the generated app account. Acting as an existing user requires an
explicit user action. This project requires consistent attribution to the
dedicated account `u/FrierenInsights`, so it requests minimal OAuth Data API
access instead.

## Required permissions

Requested OAuth scopes: `identity`, `read`, `flair`, and `submit`.

The bot is fixed to one username and one subreddit. It verifies the authenticated
identity before any submission. The community owner should grant
`u/FrierenInsights` only the moderator permissions needed for posts and flair.

## Local dry run

Python 3.11 or newer is required.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
cp .env.example .env
set -a; . ./.env; set +a
fibre-discounts-bot --dry-run
```

The dry run needs `OPENAI_API_KEY` to create a draft, but never calls Reddit.
Do not put credentials, Reddit approval correspondence, or the private MD
permission letter in this public repository.

## Production configuration

After Reddit approves the exact use case:

1. Create the approved Reddit OAuth application for `u/FrierenInsights`.
2. Add `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_REFRESH_TOKEN`, and
   `OPENAI_API_KEY` as GitHub Actions secrets.
3. Add `REDDIT_APPROVAL_GRANTED=true` as a repository Actions variable.
4. Run the workflow manually once and inspect the resulting Reddit post.
5. Leave the schedule enabled only while the offers, disclosures, sources, and
   permissions remain current.

The workflow runs at both possible UTC equivalents of 09:07 Europe/London and
the application accepts only the matching local-time run. A concurrency lock
prevents overlapping executions. Scheduled workflows in public repositories
can be disabled by GitHub after prolonged inactivity; successful daily state
commits keep this repository active, but the owner should still monitor it.

## Sources and editorial controls

Default feeds are configured in `src/fibre_bot/config.py`. A source must be an
HTTPS RSS/Atom feed from the explicit allowlist. The generator may only
paraphrase the supplied title and feed summary; it cannot browse Reddit or make
unsourced provider comparisons.

The fixed deal paragraph deliberately avoids hard-coded reward values because
offers can change. Any future numerical offer, contract-buyout claim, or
provider comparison must be supported by a current primary source and added
with a test before deployment.

## Records

`state/posted.json` stores only source URLs, publication times, and the bot's
own Reddit post IDs. No Redditor data is stored. State is committed after a
successful scheduled submission so later runners can prevent duplicates.

## Policy references

- [Reddit Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)
- [Developer Platform and accessing Reddit data](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data)
- [Reddit Data API reference](https://www.reddit.com/dev/api/)
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
