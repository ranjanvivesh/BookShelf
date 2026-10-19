from django.core.management.base import BaseCommand

from recommender.services import build_tfidf_similarity


class Command(BaseCommand):
    help = 'Recompute similar-book lists (run nightly with cron)'

    def add_arguments(self, parser):
        parser.add_argument('--top-k', type=int, default=10)

    def handle(self, *args, **options):
        count = build_tfidf_similarity(top_k=options['top_k'])
        self.stdout.write(f'Saved {count} similarity rows')
