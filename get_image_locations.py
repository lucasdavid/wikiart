import pandas as pd
import click

@click.command()
@click.argument('artist',
    type=str
    # help='name of the artist in the format of [firstname-lastname], e.g. "claude-monet".'
    )
@click.option('--output',
    default=None,
    type=str,
    help='path str of the output csv file'
    )
@click.option('--datadir',
    default='./wikiart-saved',
    type=str,
    help='the location of data directory, should contain a "meta" folder inside.',
    show_default=True
    )
@click.option('--sample_size',
    default=None,
    type=int,
    help='size of sampling without replacement.',
    show_default=True
    )
@click.option('--query',
    default=None,
    type=str,
    help='a query string executable by pandas.DataFrame, e.g. "style==\'Impressionism\'"'
    )
def main(artist, output, datadir, sample_size, query):
    ''' A tool to sample the image urls of works from an aritist \n
        e.g. python get_image_locations.py --datadir ./impressionists 
            --query 'style=="Impressionism"' --sample_size 200 claude-monet
    '''
    df_artist = pd.read_json(f'{datadir}/meta/{artist}.json')

    # query
    if query:
        df_artist = df_artist.query(query)

    # sampling
    if sample_size:
        if len(df_artist) < sample_size: with_replacement = True
        else: with_replacement = False

        image_locs = (
            df_artist.sample(sample_size, random_state=42, replace=with_replacement)
                    ['image']
                    .reset_index(drop=True)
        )
    else:
        image_locs = df_artist['image'].reset_index(drop=True)

    # output csv file
    if output:
        image_locs.to_csv(output, header=False, index=False)
    else:
        image_locs.to_csv(f'{datadir}/{artist}.csv', header=False, index=False)

if __name__ == "__main__":
    main()