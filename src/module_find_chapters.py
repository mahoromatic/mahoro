from logging import debug, info, warning, error
from datetime import datetime, timedelta
import time


from services import mangaplus
import reddit

import schedule

ignore_chapter_id = False  # for debugging purposes, normally should always be False

reddit_post_title_format = ''
reddit_post_link_format = "https://mangaplus.shueisha.co.jp/viewer/{chapter_id}"

def main(config, db, **kwargs):
    global reddit_post_title_format
    reddit_post_title_format = config.post_title

    if kwargs['debug']:
        info("Debug mode not available")
    else:
        schedule.every().hour.at(":00").do(_find_mangaplus_chapters, config, db)
        # schedule.every().day.at("23:30").do(_update_mangaplus_hiatus_manga, config, db)
        schedule.every().day.at("10:30").do(_update_mangaplus_hiatus_manga, config, db)
        schedule.every().friday.at("22:00").do(_update_mangaplus_manga, config, db)
        _find_mangaplus_chapters(config, db)
        while True:
            schedule.run_pending()
            time.sleep(1)


def _find_mangaplus_chapters(config, db):
    reddit.init_reddit(config)
    time.sleep(1)

    mangas = db.get_mangas(current_time=datetime.now())

    chapter_ids = db.get_chapter_ids()

    for manga in mangas:
        m = mangaplus.MangaplusService()
        resp = m.request_from_api(manga_id=manga.manga_id)
        if resp:
            Manga = m.get_manga_detail()
            Chapters = m.get_chapter_detail()

            if Chapters[0].chapter_id not in chapter_ids or ignore_chapter_id:
                reddit_post_title, reddit_post_link = _process_into_reddit_post(
                    config, db, manga, Chapters)
                # info(f"Reddit Post Title: {reddit_post_title}")
                # info(f"Reddit Post Link: {reddit_post_link}")
                submission = reddit.submit_link_post(
                    reddit_post_title, reddit_post_link, config.community, manga.is_nsfw)

                for Chapter in Chapters:
                    Chapter.reddit_post_id = submission["post_view"]["post"]["id"]
                    db.add_chapter(Chapter.chapter_id, Chapter.chapter_name, Chapter.chapter_number,
                                   Chapter.reddit_post_id, manga.manga_id)

            db.update_manga(manga_id=manga.manga_id,
                            next_update_time=Manga.next_update_time, is_completed=Manga.is_completed)

    time.sleep(2)

    if mangas or datetime.now().hour in [23, 0]:
        _find_new_manga(config, db)

def _process_into_reddit_post(config, db, Manga, Chapters):
    if Chapters[0].chapter_number == 0:
        chapter_number = "Extra Chapter"
    elif Chapters[0].chapter_number == 0.1:
        chapter_number = "One-Shot"
    else:
        chapter_number = f"Chapter {Chapters[0].chapter_number:g}"

    reddit_post_title = reddit_post_title_format.format(
        manga_name=Manga.manga_name, chapter_number=chapter_number)
    reddit_post_link = reddit_post_link_format.format(
        chapter_id=Chapters[0].chapter_id)

    if len(Chapters)>2:
        reddit_post_title += f" - {'Extra Chapter' if Chapters[-1].chapter_number == 0 else f'{Chapters[-1].chapter_number:g}' }"
    elif len(Chapters)==2:
        reddit_post_title += f" & {'Extra Chapter' if Chapters[1].chapter_number == 0 else f'{Chapters[1].chapter_number:g}' }"

    return reddit_post_title, reddit_post_link


def _update_mangaplus_hiatus_manga(config, db):
    info(f"Hiatus manga info update")
    mangas = db.get_mangas(completed=True)
    _update_next_update_time(config, db, mangas)


def _update_mangaplus_manga(config, db):
    info(f"Weekly manga info update")
    mangas = db.get_mangas(completed=False)
    _update_next_update_time(config, db, mangas)


def _update_next_update_time(config, db, mangas):
    m = mangaplus.MangaplusService()

    for manga in mangas:
        resp = m.request_from_api(manga_id=manga.manga_id)
        if resp:
            Manga = m.get_manga_detail()
            if Manga.next_update_time != manga.next_update_time:
                info(
                    f"Updating {Manga.manga_name}  Next Update Time:{datetime.fromtimestamp(Manga.next_update_time)}")
                db.update_manga(manga_id=Manga.manga_id,
                                next_update_time=Manga.next_update_time)
        time.sleep(3)


def _find_new_manga(config, db):
    info("Finding new manga")
    manga_re_edtion_ids = db.get_manga_re_edition(ids_only=True)
    manga_re_edtion_ids.extend(db.get_manga_ids())

    m = mangaplus.MangaplusService()

    resp = m.request_from_api(updated=True)
    if resp:
        updated_manga_ids = m.get_update_new_manga(manga_re_edtion_ids)
    else:
        error("Can't get new updated manga")
        updated_manga_ids = []

    for manga_id in updated_manga_ids:
        resp = m.request_from_api(manga_id=manga_id)
        if resp:
            Manga = m.get_manga_detail()
            Chapters = m.get_chapter_detail()

            reddit_post_title, reddit_post_link = _process_into_reddit_post(
                config, db, Manga, Chapters)
            # info(f"Reddit Post Title: {reddit_post_title}")
            # info(f"Reddit Post Link: {reddit_post_link}")
            submission = reddit.submit_link_post(
                reddit_post_title, reddit_post_link, config.community, False)

            db.add_manga(Manga.manga_id, Manga.manga_name, Manga.subreddit,
                         Manga.next_update_time, Manga.is_completed, Manga.is_nsfw)

            for Chapter in Chapters:
                Chapter.reddit_post_id = submission.id
                db.add_chapter(Chapter.chapter_id, Chapter.chapter_name, Chapter.chapter_number,
                               Chapter.reddit_post_id, manga_id)
