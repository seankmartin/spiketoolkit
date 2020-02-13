import numpy as np

import spikemetrics.metrics as metrics
from spiketoolkit.curation.thresholdcurator import ThresholdCurator

from .quality_metric import QualityMetric


class DPrime(QualityMetric):
    def __init__(self, metric_data):
        QualityMetric.__init__(self, metric_data, metric_name="d_prime")

        if not metric_data.has_pca_scores():
            raise ValueError("MetricData object must have pca scores")

    def compute_metric(self, num_channels_to_compare, max_spikes_per_cluster, seed, save_as_property):

        d_primes_epochs = []
        for epoch in self._metric_data._epochs:
            in_epoch = np.logical_and(
                self._metric_data._spike_times_pca > epoch[1],
                self._metric_data._spike_times_pca < epoch[2],
            )
            d_primes_all = metrics.calculate_pc_metrics(
                spike_clusters=self._metric_data._spike_clusters_pca[in_epoch],
                total_units=self._metric_data._total_units,
                pc_features=self._metric_data._pc_features[in_epoch, :, :],
                pc_feature_ind=self._metric_data._pc_feature_ind,
                num_channels_to_compare=num_channels_to_compare,
                max_spikes_for_cluster=max_spikes_per_cluster,
                spikes_for_nn=None,
                n_neighbors=None,
                metric_names=["d_prime"],
                seed=seed,
                verbose=self._metric_data.verbose,
            )[2]
            d_primes_list = []
            for i in self._metric_data._unit_indices:
                d_primes_list.append(d_primes_all[i])
            d_primes = np.asarray(d_primes_list)
            d_primes_epochs.append(d_primes)
        if save_as_property:
            self.save_as_property(self._metric_data._sorting, d_primes_epochs, self._metric_name)
        return d_primes_epochs

    def threshold_metric(self, threshold, threshold_sign, epoch, num_channels_to_compare, max_spikes_per_cluster, seed, save_as_property):

        assert epoch < len(self._metric_data.get_epochs()), "Invalid epoch specified"

        d_primes_epochs = self.compute_metric(num_channels_to_compare, max_spikes_per_cluster, seed, save_as_property=save_as_property)[epoch]
        threshold_curator = ThresholdCurator(
            sorting=self._metric_data._sorting, metrics_epoch=d_primes_epochs
        )
        threshold_curator.threshold_sorting(
            threshold=threshold, threshold_sign=threshold_sign
        )
        return threshold_curator