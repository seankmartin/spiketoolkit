from abc import ABC, abstractmethod
import spikeextractors as se
import numpy as np
from spikeextractors import RecordingExtractor


class FilterRecording(RecordingExtractor):
    def __init__(self, recording, chunk_size=10000, cache_chunks=False):
        if not isinstance(recording, RecordingExtractor):
            raise ValueError("'recording' must be a RecordingExtractor")
        self._recording = recording
        self._chunk_size = chunk_size
        self._cache_chunks = cache_chunks
        if cache_chunks:
            self._filtered_cache_chunks = FilteredChunkCache()
        else:
            self._filtered_cache_chunks = None
        self._traces = None
        se.RecordingExtractor.__init__(self)
        self.copy_channel_properties(recording)

    def get_channel_ids(self):
        return self._recording.get_channel_ids()

    def get_num_frames(self):
        return self._recording.get_num_frames()

    def get_sampling_frequency(self):
        return self._recording.get_sampling_frequency()

    def get_traces(self, channel_ids=None, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self.get_num_frames()
        if channel_ids is None:
            channel_ids = self.get_channel_ids()
        if isinstance(channel_ids, (int, np.integer)):
            channel_ids = [channel_ids]
        if self._chunk_size is not None:
            ich1 = int(start_frame / self._chunk_size)
            ich2 = int((end_frame - 1) / self._chunk_size)
            dt = self._recording.get_traces(start_frame=0, end_frame=1).dtype
            filtered_chunk = np.zeros((len(channel_ids), int(end_frame-start_frame)), dtype=dt)
            pos = 0
            for ich in range(ich1, ich2 + 1):
                filtered_chunk0 = self._get_filtered_chunk(ich)
                if ich == ich1:
                    start0 = start_frame - ich * self._chunk_size
                else:
                    start0 = 0
                if ich == ich2:
                    end0 = end_frame - ich * self._chunk_size
                else:
                    end0 = self._chunk_size
                chan_idx = [self.get_channel_ids().index(chan) for chan in channel_ids]
                filtered_chunk[:, pos:pos+end0-start0] = filtered_chunk0[chan_idx, start0:end0]
                pos += (end0-start0)
        else:
            filtered_chunk = self.filter_chunk(start_frame=start_frame, end_frame=end_frame)[channel_ids, :]
        return filtered_chunk

    @abstractmethod
    def filter_chunk(self, *, start_frame, end_frame):
        raise NotImplementedError('filter_chunk not implemented')

    def _get_filtered_chunk(self, ind):
        if self._cache_chunks:
            code = str(ind)
            chunk0 = self._filtered_cache_chunks.get(code)
        else:
            chunk0 = None
        if chunk0 is not None:
            return chunk0

        start0 = ind * self._chunk_size
        end0 = (ind + 1) * self._chunk_size
        chunk1 = self.filter_chunk(start_frame=start0, end_frame=end0)
        if self._cache_chunks:
            self._filtered_cache_chunks.add(code, chunk1)
        
        return chunk1
            


class FilteredChunkCache():
    def __init__(self):
        self._chunks_by_code = dict()
        self._codes = []
        self._total_size = 0
        self._max_size = 1024 * 1024 * 100

    def add(self, code, chunk):
        self._chunks_by_code[code] = chunk
        self._codes.append(code)
        self._total_size = self._total_size + chunk.size
        if self._total_size > self._max_size:
            ii = 0
            while (ii < len(self._codes)) and (self._total_size > self._max_size / 2):
                self._total_size = self._total_size - self._chunks_by_code[self._codes[ii]].size
                del self._chunks_by_code[self._codes[ii]]
                ii = ii + 1
            self._codes = self._codes[ii:]

    def get(self, code):
        if code in self._chunks_by_code:
            return self._chunks_by_code[code]
        else:
            return None
