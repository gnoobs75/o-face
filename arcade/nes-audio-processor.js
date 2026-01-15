class NESAudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = new Float32Array(32768);
        this.writeIndex = 0;
        this.readIndex = 0;

        this.port.onmessage = (e) => {
            if (e.data.type === 'samples') {
                const samples = e.data.samples;
                for (let i = 0; i < samples.length; i++) {
                    this.buffer[this.writeIndex] = samples[i];
                    this.writeIndex = (this.writeIndex + 1) % this.buffer.length;
                }
            }
        };
    }

    process(inputs, outputs, parameters) {
        const output = outputs[0];
        const left = output[0];
        const right = output[1];

        if (left && right) {
            for (let i = 0; i < left.length; i++) {
                if (this.readIndex !== this.writeIndex) {
                    left[i] = this.buffer[this.readIndex];
                    this.readIndex = (this.readIndex + 1) % this.buffer.length;
                } else {
                    left[i] = 0;
                }

                if (this.readIndex !== this.writeIndex) {
                    right[i] = this.buffer[this.readIndex];
                    this.readIndex = (this.readIndex + 1) % this.buffer.length;
                } else {
                    right[i] = 0;
                }
            }
        }

        return true;
    }
}

registerProcessor('nes-audio-processor', NESAudioProcessor);
