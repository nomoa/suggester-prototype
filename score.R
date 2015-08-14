dat = read.csv("/plat/cirrus-dump/doc_stats.csv", header=TRUE, sep=",")


# Explore if there is a ratio somewhere that could correlate with the quality of an article??
dat$headingBalance <- dat$bytes/dat$headings
dat$outLinkBalance <- dat$bytes/dat$outgoing
dat$extLinkBalance <- dat$bytes/dat$externalLinks
dat$incLinkBalance <- dat$bytes/dat$incomingLinks
dat$headingExtLinks <- dat$externalLinks/dat$headings

# Score function
score <- function(maxDocs, incomingLinksRaw, externalLinksRaw, bytesRaw, headingsRaw, redirectsRaw) {
  INCOMING_LINKS_MAX_DOCS_FACTOR = 1/10;

  EXTERNAL_LINKS_NORM = 1000;
  PAGE_SIZE_NORM = 300000;
  HEADING_NORM = 50;
  REDIRECT_NORM = 100;

  INCOMING_LINKS_WEIGHT = 0.6;
  EXTERNAL_LINKS_WEIGHT = 0.3;
  PAGE_SIZE_WEIGHT = 0.1;
  HEADING_WEIGHT = 0.2;
  REDIRECT_WEIGHT = 0.1;

  OUTGOING_LINK_BLANCE = 2000;
  HEADINGS_BALANCE = 3000;
  EXT_LINKS_BALANCE = 2000;

  SCORE_RANGE = 100000;
  # If a page gets linked by more than 1/10 of all pages.
  incLinksNorm <- maxDocs * INCOMING_LINKS_MAX_DOCS_FACTOR;

  incLinks <- scoreNormL2(incomingLinksRaw, incLinksNorm)
  extLinks <- scoreNormL2(externalLinksRaw, EXTERNAL_LINKS_NORM)
  pageSize <- scoreNormL2(bytesRaw, PAGE_SIZE_NORM)
  headings <- scoreNorm(headingsRaw, HEADING_NORM)
  redirects <- scoreNorm(redirectsRaw, REDIRECT_NORM)

  score <- incLinks * INCOMING_LINKS_WEIGHT;
  score <- score + extLinks * EXTERNAL_LINKS_WEIGHT;
  score <- score + pageSize * PAGE_SIZE_WEIGHT;
  score <- score + headings * HEADING_WEIGHT;
  score <- score + redirects * REDIRECT_WEIGHT;

  score <- score / (INCOMING_LINKS_WEIGHT + EXTERNAL_LINKS_WEIGHT + PAGE_SIZE_WEIGHT + HEADING_WEIGHT + REDIRECT_WEIGHT);


  # headingsBalance <- bytesRaw / headingsRaw;
  # headingDistance <- HEADINGS_BALANCE - headingsBalance;

  # extLinksBalance <- externalLinksRaw / bytesRaw;
  # extLinksDistance <- EXT_LINKS_BALANCE - headingsBalance;

  #score <- score * (1-1/abs(headingDistance))
  #score <- score * (1-1/abs(extLinksDistance))

  return (score * SCORE_RANGE);
}

# log2(value/norm + 1)
scoreNormL2 <- function(value, norm) {
  if(value > norm) {
    value <- norm;
  }
  return(log2((value/norm) + 1));
}

# simple ratio
scoreNorm <- function(value, norm) {
  if(value > norm) {
    value <- norm;
  }
  return(value/norm);
}

# compute the score
dat$score <- mapply(score, nrow(dat), dat$incomingLinks, dat$externalLinks, dat$bytes, dat$headings, dat$redirects );



# various stuff to explore distribution

quantile(dat$redirects, 0.999);

plot(density(dat$incomingLinks, from=0.00001), log="x", xlim=c(1,max(dat$incomingLinks)))
plot(density(dat$externalLinks, from=0.00001), log="x", xlim=c(1,max(dat$externalLinks)))
plot(density(dat$bytes, from=0.00001), log="x", xlim=c(1,max(dat$bytes)))
plot(density(dat$headings, from=0.00001), log="x", xlim=c(1,max(dat$headings)))
plot(density(dat$redirects, from=0.00001), log="x", xlim=c(1,max(dat$redirects)))


plot(density(dat$headingBalance))
plot(density(dat$headings))
plot(dat$incomingLinks + 10,dat$externalLinks + 10, log="yx", cex=0.2)
plot(dat$incomingLinks + 10, dat$bytes + 10, log="yx", cex=0.2)
plot(dat$incomingLinks + 10, dat$headings + 10, log="yx", cex=0.2)
plot(dat$incomingLinks + 10, dat$headings + 10, log="yx", cex=0.2)
plot(dat$incomingLinks + 10, dat$redirects + 10, log="yx", cex=0.2)
